# dc

A thin CRUD wrapper over the Discord REST API. Each command maps to one
endpoint, passes through the flags you give it, and prints the API's JSON
response verbatim. No workflows, no file conventions, no opinions about content.

What it does handle is the plumbing every caller would otherwise redo: the
token, the Cloudflare user-agent that Discord's edge requires, pagination,
rate-limit backoff, and the encodings Discord demands (base64 data-URI cover
images, `location` nested inside `entity_metadata`).

## Addressing

The server defaults to `$DISCORD_GUILD_ID`; `--guild` overrides it for a single
command. With neither, commands exit rather than guess.

Both `--guild` and `<channel>` take an id or a case-insensitive name fragment.
Punctuation and emoji are ignored, so `server-admins` matches `🔨server-admins`.
An id is used as-is, so only name fragments cost an extra lookup request.
Ambiguous fragments exit with the candidate list.

## Commands

```sh
dc auth whoami                       # GET /users/@me

dc guilds list                       # GET /users/@me/guilds
dc guilds get                        # GET /guilds/{id}

dc channels list                     # GET /guilds/{id}/channels
dc channels get    <channel>         # GET /channels/{id}
dc channels delete <channel>         # DELETE /channels/{id}

dc messages list   <channel> [--before ID] [--after ID] [--limit N] [--all]
dc messages get    <channel> <message_id>
dc messages send   <channel> (--text "..." | --text-file PATH) [--reply-to ID]
dc messages edit   <channel> <message_id> (--text "..." | --text-file PATH)
dc messages delete <channel> <message_id>

dc threads create  <channel> --name NAME [--message ID] [--archive MIN]

dc events list
dc events get      <event_id>
dc events create   --name N --start ISO [--end ISO] [--location L]
                   [--channel C] [--type external|voice|stage]
                   [--description D] [--image PATH] [--privacy N]
dc events edit     <event_id> [any create flag] [--status scheduled|active|completed|canceled]
dc events delete   <event_id>
```

Output is the raw API object, so `messages list` returns every field Discord
sends (reactions, mentions, `edited_timestamp`, and the rest), not a subset.
Pipe to `jq` to narrow it.

### Notes per resource

**messages** — `--text-file` reads the message *text* from a file; it does not
upload an attachment (there is no multipart support yet). Bodies over Discord's
2000-character cap are rejected before the request is sent. `list` returns
newest-first, matching the API; `--all` pages the full history and ignores
`--limit`.

**threads** — with `--message`, the thread hangs off that message and **takes
the message's id as its own**. Without it, you get a standalone public thread.
A thread is a channel, so post into it with `dc messages send <thread_id>` and
remove it with `dc channels delete <thread_id>`.

Deleting a thread's starter message does **not** delete the thread.

**events** — default `--type external` and `--privacy 2` (guild only), the
common case. External events need `--end` and `--location`; voice and stage
events need `--channel` instead. Only the flags you pass are sent, and Discord
validates the combination.

Timestamps are **local time with an explicit UTC offset** — `-07:00` for PDT,
`-08:00` for PST. Do not pre-convert to UTC. A timestamp without an offset is
rejected before any API call.

## Permissions

Failures surface Discord's own error body, e.g.
`403 POST /channels/123/messages` / `{"message": "Missing Permissions", "code": 50013}`.
Note that a server-wide grant can still be overridden per channel, which is the
usual cause of a 403 on one channel while another works.

| Command | Needs |
|---------|-------|
| `messages list/get` | View Channel, Read Message History |
| `messages send/edit` | Send Messages |
| `messages delete` | own message, else Manage Messages |
| `threads create` | Create Public Threads |
| `channels delete` | Manage Channels / Manage Threads |
| `events create` | Create Events |
| `events edit/delete` | Manage Events |

## Config

`$DISCORD_BOT_TOKEN` and `$DISCORD_GUILD_ID`, else the first `.env` defining
each key, searched in: the current dir, `clis/`, then the repo root. Because the
current directory is searched first, identity can depend on where you run it
from — export the variables explicitly if that matters.
