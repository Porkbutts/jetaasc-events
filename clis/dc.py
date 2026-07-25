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
  dc messages send    <channel> (--text "..." | --text-file PATH) [--reply-to ID]
  dc messages edit    <channel> <message_id> (--text "..." | --text-file PATH)
  dc messages delete  <channel> <message_id>

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

Config is read from the environment, else the first .env containing the key,
searched in: the current dir, this script's dir, then its parent.
"""
import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

API = "https://discord.com/api/v10"
# Discord's Cloudflare edge 403s (error 1010) any request without a DiscordBot UA.
UA = "DiscordBot (https://jetaasc.org, 1.0)"
# realpath, not abspath: this script is invoked through a symlink on PATH, and
# abspath would resolve HERE to the symlink's dir instead of the real one.
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
LIMIT = 2000                        # Discord's per-message character cap
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
    hits = [i for i in items if _norm(ref) in _norm(i["name"])]
    if len(hits) == 1:
        return hits[0]["id"]
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
    return _pick(ref, req("GET", "/users/@me/guilds"), "guild")


def resolve_channel(gid, ref):
    if ref.isdigit():
        return ref
    return _pick(ref, req("GET", f"/guilds/{gid}/channels"), "channel")


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
    s = m.add_mutually_exclusive_group(required=True)
    s.add_argument("--text"); s.add_argument("--text-file", metavar="PATH",
                                             help="Read the message text from a file")
    m.add_argument("--reply-to", metavar="ID")
    m = msgs.add_parser("edit", parents=[g], help="PATCH /channels/{id}/messages/{id}")
    m.add_argument("channel"); m.add_argument("message_id")
    s = m.add_mutually_exclusive_group(required=True)
    s.add_argument("--text"); s.add_argument("--text-file", metavar="PATH")
    m = msgs.add_parser("delete", parents=[g], help="DELETE /channels/{id}/messages/{id}")
    m.add_argument("channel"); m.add_argument("message_id")

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
    global TOK
    a = build_parser().parse_args()
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
        body = {"content": text_of(a)}
        if a.reply_to:
            body["message_reference"] = {"message_id": a.reply_to}
        out(req("POST", f"/channels/{cid}/messages", body))
    elif key == "messages edit":
        out(req("PATCH", f"/channels/{cid}/messages/{mid}", {"content": text_of(a)}))
    elif key == "messages delete":
        req("DELETE", f"/channels/{cid}/messages/{mid}")
        out({"deleted": mid})
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
