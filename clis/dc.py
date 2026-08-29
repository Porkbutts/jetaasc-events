#!/usr/bin/env python3
"""dc — a thin CRUD wrapper over the Discord REST API.

No workflows, no conventions, no opinions about content. Each command maps to
one endpoint, passes through whatever flags you give it, and prints the API's
JSON response verbatim. What it does handle is the plumbing every caller would
otherwise redo: the token, the Cloudflare user-agent, pagination, rate-limit
backoff, and the encodings Discord requires (base64 data-URI cover images,
location tucked into entity_metadata).

  dc auth whoami

  dc guilds list
  dc guilds get

  dc channels list
  dc channels get     <channel>
  dc channels delete  <channel>          (threads are channels; this removes one)

  dc messages list    <channel> [--before ID | --after ID] [--limit N | --all]
  dc messages get     <channel> <message_id>
  dc messages send    <channel> [--text "..." | --text-file PATH] [--reply-to ID]
                      [--poll-question Q --poll-answer "A[|emoji]" ...
                       [--poll-duration H] [--poll-multiselect] | --poll-json J]
  dc messages edit    <channel> <message_id> (--text "..." | --text-file PATH)
  dc messages delete  <channel> <message_id>

  dc reactions add    <channel> <message_id> <emoji>
  dc reactions remove <channel> <message_id> <emoji> [--user ID]
  dc reactions list   <channel> <message_id> <emoji> [--limit N]
  dc reactions clear  <channel> <message_id> [<emoji>]

  dc polls voters     <channel> <message_id> <answer_id> [--limit N] [--after ID]
  dc polls expire     <channel> <message_id>

  dc threads create   <channel> --name NAME [--message ID] [--archive MIN]

  dc events list
  dc events get       <event_id>
  dc events create    --name N --start ISO [--end ISO] [--location L]
                      [--channel C] [--type external|voice|stage]
                      [--description D] [--image PATH] [--privacy N]
  dc events edit      <event_id> [any create flag] [--status scheduled|active|completed|canceled]
  dc events delete    <event_id>

The server defaults to $DISCORD_GUILD_ID; --guild overrides it for one command.
Both --guild and <channel> accept an id or a case-insensitive name fragment;
emoji and punctuation are ignored, so "server-admins" matches "🔨server-admins".
An id is used as-is, so only name fragments cost a lookup request.

<emoji> takes a standard emoji character, or for a custom one either its
<:name:id> form or a bare name, which is looked up in the guild's emoji.

Config is read from the environment, else the first .env containing the key,
searched in: the current dir, this script's dir, then its parent.

  DISCORD_BOT_TOKEN   required
  DISCORD_GUILD_ID    default guild, overridable per command with --guild
  DISCORD_USER_AGENT  optional, defaults to "DiscordBot (dc, 1.0)". Anything
                      but urllib's own UA gets through, but Discord asks bots
                      to send "DiscordBot ($url, $version)".
"""
import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

API = "https://discord.com/api/v10"
# Discord's Cloudflare edge 403s (error 1010) urllib's default UA, so sending
# one is not optional. Anything else is let through, but Discord's docs ask bots
# for "DiscordBot ($url, $version)", so that is the shape of the default.
# Set $DISCORD_USER_AGENT to identify your own bot.
DEFAULT_UA = "DiscordBot (dc, 1.0)"
UA = DEFAULT_UA  # main replaces this from $DISCORD_USER_AGENT if one is set
# realpath, not abspath: this script is invoked through a symlink on PATH, and
# abspath would resolve HERE to the symlink's dir instead of the real one.
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
LIMIT = 2000                        # Discord's per-message character cap
POLL_Q, POLL_A = 300, 55            # poll question / answer character caps
POLL_ANSWERS = 10                   # answers per poll
POLL_HOURS = 768                    # poll duration cap, 32 days
ARCHIVE = (60, 1440, 4320, 10080)   # thread auto-archive minutes Discord accepts
ENTITY = {"stage": 1, "voice": 2, "external": 3}
STATUS = {"scheduled": 1, "active": 2, "completed": 3, "canceled": 4}


def config(key):
    """Environment first, then the first .env that defines the key."""
    if os.environ.get(key):
        return os.environ[key]
    for path in (".env", os.path.join(HERE, ".env"), os.path.join(ROOT, ".env")):
        if os.path.exists(path):
            for line in open(path):
                line = line.strip()
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip()
    return None


TOK = None  # filled in main so --help never needs a token


def req(method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    # Adding a reaction is a bodyless PUT, and urllib sends no Content-Length
    # when data is None, which Discord answers with a 411.
    if data is None and method == "PUT":
        data = b""
    r = urllib.request.Request(
        f"{API}{path}", data=data, method=method,
        headers={"Authorization": f"Bot {TOK}", "User-Agent": UA,
                 "Content-Type": "application/json"})
    for _ in range(6):
        try:
            with urllib.request.urlopen(r) as resp:
                return json.load(resp) if resp.status != 204 else {}
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(float(e.headers.get("Retry-After", 2)) + 0.5)
                continue
            # Surface Discord's own error body; it names the offending field.
            sys.exit(f"{e.code} {method} {path}\n{e.read().decode()[:600]}")
    sys.exit("rate-limited out")


def out(obj):
    print(json.dumps(obj, indent=1, ensure_ascii=False))


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _pick(ref, items, what):
    """The matched item, not its id: a custom emoji is addressed by name:id."""
    hits = [i for i in items if _norm(ref) in _norm(i["name"])]
    if len(hits) == 1:
        return hits[0]
    listing = ", ".join(f'{i["name"]} ({i["id"]})' for i in items)
    if not hits:
        sys.exit(f"No {what} matches '{ref}'. Have: {listing}")
    sys.exit(f"'{ref}' is ambiguous: " + ", ".join(i["name"] for i in hits))


def resolve_guild(ref):
    """$DISCORD_GUILD_ID by default; --guild overrides it for one command."""
    ref = ref or config("DISCORD_GUILD_ID")
    if not ref:
        sys.exit("No guild. Set $DISCORD_GUILD_ID or pass --guild.")
    if ref.isdigit():
        return ref
    return _pick(ref, req("GET", "/users/@me/guilds"), "guild")["id"]


def resolve_channel(gid, ref):
    if ref.isdigit():
        return ref
    return _pick(ref, req("GET", f"/guilds/{gid}/channels"), "channel")["id"]


def resolve_emoji(gid, ref):
    """The path segment Discord wants: the raw character for a standard emoji,
    name:id for a custom one. Both are percent-encoded by the caller.

    A :shortcode: is not something the API accepts, and a standard emoji cannot
    be looked up by name, so a bare ascii name is taken to mean a custom emoji
    and resolved against the guild's set the way channels are.
    """
    ref = ref.strip()
    mention = re.fullmatch(r"<a?:([^:]+):(\d+)>", ref)   # <:name:id>, <a:name:id>
    if mention:
        return f"{mention.group(1)}:{mention.group(2)}"
    if re.fullmatch(r"[^:]+:\d+", ref):                  # already name:id
        return ref
    if not ref.isascii():                                # standard emoji
        return ref
    emoji = _pick(ref.strip(":"), req("GET", f"/guilds/{gid}/emojis"), "emoji")
    return f'{emoji["name"]}:{emoji["id"]}'


def emoji_object(gid, ref):
    """The partial emoji a poll answer takes: an id for a custom emoji, a name
    for a standard one. Not the name:id path segment reactions use."""
    resolved = resolve_emoji(gid, ref)
    return ({"id": resolved.split(":")[-1]} if ":" in resolved
            else {"name": resolved})


def poll_body(a, gid):
    """The poll object for Create Message, or None if no poll flags were given.

    Discord validates the combination; the checks here are the ones it answers
    with an opaque 400, or silently truncates.
    """
    if a.poll_json:
        if a.poll_question or a.poll_answer:
            sys.exit("Use --poll-json or the --poll-* flags, not both.")
        try:
            return json.loads(a.poll_json)
        except json.JSONDecodeError as e:
            sys.exit(f"--poll-json is not valid JSON: {e}")
    if not (a.poll_question or a.poll_answer):
        return None
    if not (a.poll_question and a.poll_answer):
        sys.exit("A poll needs --poll-question and at least one --poll-answer.")
    if len(a.poll_question) > POLL_Q:
        sys.exit(f"Question is {len(a.poll_question)} chars, over Discord's "
                 f"{POLL_Q} cap.")
    if len(a.poll_answer) > POLL_ANSWERS:
        sys.exit(f"{len(a.poll_answer)} answers, over Discord's cap of "
                 f"{POLL_ANSWERS}.")
    if a.poll_duration is not None and not 1 <= a.poll_duration <= POLL_HOURS:
        sys.exit(f"--poll-duration must be 1-{POLL_HOURS} hours (32 days), got "
                 f"{a.poll_duration}.")

    answers = []
    for spec in a.poll_answer:
        text, _, emoji = spec.partition("|")
        text = text.strip()
        if not text:
            sys.exit(f"Answer {spec!r} has no text.")
        if len(text) > POLL_A:
            sys.exit(f"Answer {text!r} is {len(text)} chars, over Discord's "
                     f"{POLL_A} cap.")
        media = {"text": text}
        if emoji.strip():
            media["emoji"] = emoji_object(gid, emoji.strip())
        answers.append({"poll_media": media})

    poll = {"question": {"text": a.poll_question}, "answers": answers}
    if a.poll_duration is not None:
        poll["duration"] = a.poll_duration
    if a.poll_multiselect:
        poll["allow_multiselect"] = True
    return poll


def list_messages(cid, before, after, limit, all_):
    """Pages the endpoint. Each batch arrives newest-first, matching the API's
    own order; --after walks forward from its id, otherwise we walk backward."""
    out_, cursor = [], None
    while True:
        want = 100 if all_ else min(100, limit - len(out_))
        params = {"limit": want}
        if after:
            params["after"] = cursor or after
        elif cursor or before:
            params["before"] = cursor or before
        q = "&".join(f"{k}={v}" for k, v in params.items())
        batch = req("GET", f"/channels/{cid}/messages?{q}")
        if not batch:
            break
        out_.extend(batch)
        # Page from the end we are walking toward: the oldest id of the batch
        # going backward, the newest going forward. Using the oldest id in both
        # directions is what made --after silently double back after batch one.
        cursor = batch[0]["id"] if after else batch[-1]["id"]
        if not all_ and len(out_) >= limit:
            return out_[:limit]
        if len(batch) < want:
            break
        time.sleep(0.3)
    return out_


def text_of(a):
    text = a.text if a.text is not None else open(a.text_file).read()
    if len(text) > LIMIT:
        sys.exit(f"Message is {len(text)} chars, over Discord's {LIMIT} cap.")
    return text


def iso(ts, flag):
    """Discord rejects a non-ISO8601 timestamp with an opaque 400; catch it here.

    A naive timestamp is rejected too. Discord reads one as UTC, so an event
    written in local time would land hours off with no error anywhere.
    """
    try:
        parsed = datetime.fromisoformat(ts)
    except ValueError:
        sys.exit(f"--{flag} must be ISO8601 with a UTC offset, e.g. "
                 f"2026-08-15T18:00:00-07:00 (got {ts!r})")
    if parsed.tzinfo is None:
        sys.exit(f"--{flag} has no UTC offset, so Discord would read {ts!r} as "
                 f"UTC and shift the event. Add one, e.g. {ts}-07:00")
    return ts


def image_data_uri(path):
    """Discord takes images in JSON bodies as base64 data URIs."""
    ext = os.path.splitext(path)[1].lower().lstrip(".") or "png"
    mime = {"jpg": "jpeg", "jpe": "jpeg"}.get(ext, ext)
    with open(path, "rb") as f:
        return f"data:image/{mime};base64," + base64.b64encode(f.read()).decode()


def poll_flags(p):
    """Poll fields on messages send. Discord has no endpoint for editing a poll,
    so these exist on send only."""
    p.add_argument("--poll-question", metavar="TEXT",
                   help=f"Poll question, {POLL_Q} chars max")
    p.add_argument("--poll-answer", action="append", metavar="TEXT[|EMOJI]",
                   help=f"An answer, {POLL_A} chars max. Repeatable, up to "
                        f"{POLL_ANSWERS}. An emoji after | takes the same forms "
                        f"as a reaction's")
    p.add_argument("--poll-duration", type=int, metavar="HOURS",
                   help=f"1-{POLL_HOURS} (32 days) [default: Discord's 24]")
    p.add_argument("--poll-multiselect", action="store_true",
                   help="Let voters pick more than one answer")
    p.add_argument("--poll-json", metavar="JSON",
                   help="The whole poll object as JSON, instead of the flags above")


def event_body(a, gid):
    """Only the flags actually passed; Discord validates the combination."""
    b = {}
    if a.name:
        b["name"] = a.name
    if a.start:
        b["scheduled_start_time"] = iso(a.start, "start")
    if a.end:
        b["scheduled_end_time"] = iso(a.end, "end")
    if a.description:
        b["description"] = a.description
    if a.privacy:
        b["privacy_level"] = a.privacy
    if a.type:
        b["entity_type"] = ENTITY[a.type]
    if a.location:
        b["entity_metadata"] = {"location": a.location}
    if a.channel:
        b["channel_id"] = resolve_channel(gid, a.channel)
    if a.image:
        b["image"] = image_data_uri(a.image)
    if getattr(a, "status", None):
        b["status"] = STATUS[a.status]
    return b


def event_flags(p, required):
    p.add_argument("--name", required=required)
    p.add_argument("--start", required=required,
                   help="ISO8601, e.g. 2026-08-15T18:00:00-07:00")
    p.add_argument("--end", help="ISO8601; Discord requires it for external events")
    p.add_argument("--location", help="Venue; external events only")
    p.add_argument("--channel", help="Voice/stage channel; those event types only")
    p.add_argument("--type", choices=ENTITY, help="Event type [default: external]")
    p.add_argument("--description")
    p.add_argument("--image", metavar="PATH", help="Cover image (PNG, JPG, GIF, WebP)")
    p.add_argument("--privacy", type=int, help="privacy_level [default: 2, guild only]")


def build_parser():
    p = argparse.ArgumentParser(
        prog="dc", description="Thin CRUD wrapper over the Discord REST API.",
        epilog="Run 'dc <resource> <action> --help' for details.")
    res = p.add_subparsers(dest="res", metavar="<resource>", required=True)

    # --guild rides on each command rather than the root parser, so it can be
    # written after the action: dc messages send general --guild X --text hi
    g = argparse.ArgumentParser(add_help=False)
    g.add_argument("--guild", help="Guild id or name fragment, overriding "
                                   "$DISCORD_GUILD_ID for this command")

    def actions(name, help_):
        return res.add_parser(name, help=help_).add_subparsers(
            dest="act", metavar="<action>", required=True)

    auth = actions("auth", "Token identity")
    auth.add_parser("whoami", help="GET /users/@me")

    guilds = actions("guilds", "Servers")
    guilds.add_parser("list", help="GET /users/@me/guilds")
    guilds.add_parser("get", parents=[g], help="GET /guilds/{id}")

    chans = actions("channels", "Channels")
    chans.add_parser("list", parents=[g], help="GET /guilds/{id}/channels")
    c = chans.add_parser("get", parents=[g], help="GET /channels/{id}")
    c.add_argument("channel")
    # Threads are channels, so this is also how a thread is removed.
    c = chans.add_parser("delete", parents=[g], help="DELETE /channels/{id}")
    c.add_argument("channel")

    msgs = actions("messages", "Messages")
    m = msgs.add_parser("list", parents=[g], help="GET /channels/{id}/messages")
    m.add_argument("channel")
    # Each pair is one choice, not a precedence: before this fix the loser was
    # accepted and then dropped on the floor.
    w = m.add_mutually_exclusive_group()
    w.add_argument("--before", metavar="ID"); w.add_argument("--after", metavar="ID")
    h = m.add_mutually_exclusive_group()
    # default stays None so argparse can tell "--limit 50" from an unpassed flag
    h.add_argument("--limit", type=int, help="[default: 50]")
    h.add_argument("--all", action="store_true", help="Page the channel out")
    m = msgs.add_parser("get", parents=[g], help="GET /channels/{id}/messages/{id}")
    m.add_argument("channel"); m.add_argument("message_id")
    m = msgs.add_parser("send", parents=[g], help="POST /channels/{id}/messages")
    m.add_argument("channel")
    # Not required=True any more: a message may be text, a poll, or both.
    s = m.add_mutually_exclusive_group()
    s.add_argument("--text"); s.add_argument("--text-file", metavar="PATH",
                                             help="Read the message text from a file")
    m.add_argument("--reply-to", metavar="ID")
    poll_flags(m)
    m = msgs.add_parser("edit", parents=[g], help="PATCH /channels/{id}/messages/{id}")
    m.add_argument("channel"); m.add_argument("message_id")
    s = m.add_mutually_exclusive_group(required=True)
    s.add_argument("--text"); s.add_argument("--text-file", metavar="PATH")
    m = msgs.add_parser("delete", parents=[g], help="DELETE /channels/{id}/messages/{id}")
    m.add_argument("channel"); m.add_argument("message_id")

    rx = actions("reactions", "Reactions")
    RX = "/channels/{id}/messages/{id}/reactions"
    r = rx.add_parser("add", parents=[g], help=f"PUT {RX}/{{emoji}}/@me")
    r.add_argument("channel"); r.add_argument("message_id"); r.add_argument("emoji")
    r = rx.add_parser("remove", parents=[g], help=f"DELETE {RX}/{{emoji}}/{{user|@me}}")
    r.add_argument("channel"); r.add_argument("message_id"); r.add_argument("emoji")
    r.add_argument("--user", metavar="ID",
                   help="Whose reaction to remove [default: the bot's own]")
    r = rx.add_parser("list", parents=[g], help=f"GET {RX}/{{emoji}}")
    r.add_argument("channel"); r.add_argument("message_id"); r.add_argument("emoji")
    r.add_argument("--limit", type=int, default=100, help="Users to return [default: 100]")
    r = rx.add_parser("clear", parents=[g], help=f"DELETE {RX}[/{{emoji}}]")
    r.add_argument("channel"); r.add_argument("message_id")
    r.add_argument("emoji", nargs="?", help="Omit to clear every reaction")

    po = actions("polls", "Polls")
    PO = "/channels/{id}/polls/{message_id}"
    o = po.add_parser("voters", parents=[g],
                      help=f"GET {PO}/answers/{{answer_id}}")
    o.add_argument("channel"); o.add_argument("message_id")
    o.add_argument("answer_id", help="1-based, in the order the answers were sent")
    o.add_argument("--limit", type=int, help="Users to return, 1-100 [default: 25]")
    o.add_argument("--after", metavar="ID", help="Page from this user id")
    o = po.add_parser("expire", parents=[g], help=f"POST {PO}/expire")
    o.add_argument("channel"); o.add_argument("message_id")

    th = actions("threads", "Threads")
    t = th.add_parser("create", parents=[g], help="POST /channels/{id}[/messages/{id}]/threads")
    t.add_argument("channel"); t.add_argument("--name", required=True)
    t.add_argument("--message", metavar="ID", help="Hang the thread off this message")
    t.add_argument("--archive", type=int, default=10080, choices=ARCHIVE,
                   help="auto_archive_duration in minutes")

    ev = actions("events", "Scheduled events")
    ev.add_parser("list", parents=[g], help="GET /guilds/{id}/scheduled-events")
    e = ev.add_parser("get", parents=[g], help="GET /guilds/{id}/scheduled-events/{id}")
    e.add_argument("event_id")
    e = ev.add_parser("create", parents=[g], help="POST /guilds/{id}/scheduled-events")
    event_flags(e, required=True)
    e = ev.add_parser("edit", parents=[g], help="PATCH /guilds/{id}/scheduled-events/{id}")
    e.add_argument("event_id")
    event_flags(e, required=False)
    e.add_argument("--status", choices=STATUS)
    e = ev.add_parser("delete", parents=[g], help="DELETE /guilds/{id}/scheduled-events/{id}")
    e.add_argument("event_id")
    return p


def main():
    global TOK, UA
    a = build_parser().parse_args()
    UA = config("DISCORD_USER_AGENT") or DEFAULT_UA
    TOK = config("DISCORD_BOT_TOKEN")
    if not TOK:
        sys.exit("No token. Set $DISCORD_BOT_TOKEN or put DISCORD_BOT_TOKEN=... in a .env")
    key = f"{a.res} {a.act}"

    if key == "auth whoami":
        return out(req("GET", "/users/@me"))
    if key == "guilds list":
        return out(req("GET", "/users/@me/guilds"))

    gid = resolve_guild(a.guild)
    cid = resolve_channel(gid, a.channel) if getattr(a, "channel", None) else None
    mid = getattr(a, "message_id", None)
    eid = getattr(a, "event_id", None)
    EV = f"/guilds/{gid}/scheduled-events"

    if key == "guilds get":
        out(req("GET", f"/guilds/{gid}"))
    elif key == "channels list":
        out(req("GET", f"/guilds/{gid}/channels"))
    elif key == "channels get":
        out(req("GET", f"/channels/{cid}"))
    elif key == "channels delete":
        out(req("DELETE", f"/channels/{cid}"))
    elif key == "messages list":
        if a.limit is not None and a.limit < 1:
            sys.exit(f"--limit must be at least 1 (got {a.limit})")
        out(list_messages(cid, a.before, a.after,
                          50 if a.limit is None else a.limit, a.all))
    elif key == "messages get":
        out(req("GET", f"/channels/{cid}/messages/{mid}"))
    elif key == "messages send":
        body = {}
        if a.text is not None or a.text_file:
            body["content"] = text_of(a)
        poll = poll_body(a, gid)
        if poll:
            body["poll"] = poll
        if not body:
            sys.exit("Nothing to send. Pass --text/--text-file, poll flags, or both.")
        if a.reply_to:
            body["message_reference"] = {"message_id": a.reply_to}
        out(req("POST", f"/channels/{cid}/messages", body))
    elif key == "messages edit":
        out(req("PATCH", f"/channels/{cid}/messages/{mid}", {"content": text_of(a)}))
    elif key == "messages delete":
        req("DELETE", f"/channels/{cid}/messages/{mid}")
        out({"deleted": mid})
    elif a.res == "reactions":
        base = f"/channels/{cid}/messages/{mid}/reactions"
        # quote(safe="") so a custom emoji's colon and a standard one's bytes
        # both survive as one path segment.
        emoji = (urllib.parse.quote(resolve_emoji(gid, a.emoji), safe="")
                 if getattr(a, "emoji", None) else None)
        if a.act == "add":
            req("PUT", f"{base}/{emoji}/@me")
            out({"reacted": a.emoji, "message": mid})
        elif a.act == "remove":
            req("DELETE", f"{base}/{emoji}/{a.user or '@me'}")
            out({"unreacted": a.emoji, "message": mid, "user": a.user or "@me"})
        elif a.act == "list":
            out(req("GET", f"{base}/{emoji}?limit={a.limit}"))
        else:
            req("DELETE", f"{base}/{emoji}" if emoji else base)
            out({"cleared": a.emoji or "all", "message": mid})
    elif a.res == "polls":
        base = f"/channels/{cid}/polls/{mid}"
        if a.act == "voters":
            q = [] if a.limit is None else [f"limit={a.limit}"]
            if a.after:
                q.append(f"after={a.after}")
            qs = f"?{'&'.join(q)}" if q else ""
            out(req("GET", f"{base}/answers/{a.answer_id}{qs}"))
        else:
            out(req("POST", f"{base}/expire"))
    elif key == "threads create":
        path = (f"/channels/{cid}/messages/{a.message}/threads" if a.message
                else f"/channels/{cid}/threads")
        body = {"name": a.name, "auto_archive_duration": a.archive}
        if not a.message:
            body["type"] = 11  # PUBLIC_THREAD; required when not off a message
        out(req("POST", path, body))
    elif key == "events list":
        out(req("GET", EV))
    elif key == "events get":
        out(req("GET", f"{EV}/{eid}"))
    elif key == "events create":
        body = event_body(a, gid)
        body.setdefault("entity_type", ENTITY["external"])
        body.setdefault("privacy_level", 2)
        out(req("POST", EV, body))
    elif key == "events edit":
        body = event_body(a, gid)
        if not body:
            # An empty PATCH echoes the event back untouched, which reads as a
            # successful edit. Say nothing changed instead.
            sys.exit("Nothing to edit. Pass at least one field to change.")
        out(req("PATCH", f"{EV}/{eid}", body))
    elif key == "events delete":
        req("DELETE", f"{EV}/{eid}")
        out({"deleted": eid})
    else:
        # Reachable only by adding a subcommand without a branch here. Without
        # this the process would exit 0 having printed nothing.
        sys.exit(f"No handler for '{key}'. This is a bug in dc.")


if __name__ == "__main__":
    main()
