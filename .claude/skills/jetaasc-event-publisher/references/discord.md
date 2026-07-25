# Discord Publishing

## Server
JETAASC Discord Server — guild ID `1066185009695838268`

## Tool
Use the `dc` CLI (on PATH). It posts as the **JETAASC Assistant** bot.
Run `dc events create --help` for the full flag list.

The guild defaults to `$DISCORD_GUILD_ID` (already set to the ID above in the
repo `.env`), so no guild argument is needed. Pass `--guild` only to target a
different server for one command.

## Create the Event

```bash
dc events create \
  --name "JETAASC Boba Banter" \
  --start 2026-08-22T11:00:00-07:00 \
  --end   2026-08-22T13:00:00-07:00 \
  --location "3CAT Handcrafted Beverage, 2481 Park Ave, Tustin, CA 92782" \
  --description "Join us for boba!

Cost: Free
RSVP: https://partiful.com/e/..." \
  --image /tmp/event-flyer.png
```

Prints the shareable event URL (`https://discord.com/events/{guild}/{event_id}`)
on success — capture it for the newsletter and other platforms.

| Flag | Required | Notes |
|------|----------|-------|
| `--name` | ✓ | Event title |
| `--start` | ✓ | ISO8601 **with UTC offset** — see below |
| `--end` | ✓ | ISO8601; Discord requires an end time for venue events |
| `--location` | ✓ | Venue name and address |
| `--description` | | Include cost and RSVP link |
| `--image` | | Local path to cover image (PNG, JPG, GIF, WebP) |

## Timestamps

Unlike the Partiful CLI, `dc` takes **local time with an explicit offset** — do
not convert to UTC. Use `-07:00` for PDT (Mar-Nov) and `-08:00` for PST
(Nov-Mar). A timestamp without an offset is rejected before any API call.

## Handling Flyer URLs

`--image` needs a local file. If the flyer is a URL, download it first:

```bash
curl -L -o /tmp/event-flyer.png "https://example.com/image.png"
```

## Other Commands

```bash
dc events list                                  # confirm what's scheduled
dc events delete <event_id>                     # remove a mistaken event
```

To also announce the event as a message (separate from the event listing):

```bash
dc messages send announcements --text "..."     # 2000 char cap
```

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `403 creating event` | Bot role lacks **Create Events** | Server Settings > Roles > JETAASC Assistant; enable *Create Events* (and *Manage Events* to edit/delete) |
| `--start must be ISO8601...` | Missing UTC offset | Append `-07:00` (PDT) or `-08:00` (PST) |
| `'<name>' is ambiguous` | Guild/channel name fragment matched several | Use the numeric ID |
