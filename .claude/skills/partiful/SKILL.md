---
name: partiful
description: Create, update, get, and delete events on Partiful using the CLI at clis/partiful.py. Use when user wants to publish, create, update, or delete a Partiful event. Triggers include "partiful", "create partiful event", "publish to partiful", or any Partiful-related task.
---

# Partiful Event Manager

Manage JETAASC events on Partiful using the CLI at `clis/partiful.py`.

## CLI Location

```
clis/partiful.py
```

No external dependencies — uses Python stdlib only (`urllib`, `json`, `argparse`).

## Authentication

Auth tokens are stored at `clis/.partiful-auth.json` (gitignored). If the file exists and the refresh token is valid, all commands work automatically.

### If auth is expired or missing

Use the two-step non-interactive flow (since `input()` doesn't work in Bash tool):

```bash
# Step 1: Send SMS code — ask the user for their phone number first
python3 clis/partiful.py send-code <PHONE_NUMBER>

# Step 2: Ask user for the code, then complete login
python3 clis/partiful.py login <PHONE_NUMBER> --code <CODE>
```

**Important:** You cannot call `login` without `--code` because that triggers interactive `input()`. Always use `send-code` first, ask the user for the code via `AskUserQuestion`, then call `login` with `--code`.

## Commands

### Create Event

```bash
python3 clis/partiful.py create \
  --title "Event Title" \
  --date 2026-03-20 \
  --time 01:00 \
  --end-date 2026-03-20 \
  --end-time 04:00 \
  --timezone "America/Los_Angeles" \
  --location "Venue Name, City" \
  --description "Event description" \
  --theme champagne \
  --effect sparkles \
  --image /path/to/flyer.png \
  --public
```

**Date/time are in UTC.** Convert from Pacific time:
- PST (Nov-Mar): add 8 hours (6pm PST = 02:00 next day UTC)
- PDT (Mar-Nov): add 7 hours (6pm PDT = 01:00 next day UTC)

Returns JSON with `eventId` and `url` (e.g., `https://partiful.com/e/{eventId}`).

**Shell escaping caveat:** The Bash tool sandbox escapes `!` to `\!` in arguments. To avoid this, wrap text arguments containing `!` in a heredoc:

```bash
python3 clis/partiful.py create \
  --title "$(cat <<'EOF'
My Event!
EOF
)" \
  --description "$(cat <<'EOF'
Join us! It will be fun!
EOF
)" \
  # ... other args
```

Available themes: `aquamarine`, `aquatica`, `aurora`, `beach`, `beer`, `blacklight`, `bokeh`, `bubblegum`, `candy`, `champagne`, `cloudflow`, `crystal`, `customColor`, `darkSky`, `daybreak`, `forest`, `galaxy`, `girlyMac`, `golden`, `grass`, `ice`, `ink`, `kaleidoscope`, `karaoke`, `komorebi`, `lavaRave`, `lofiGrass`, `meadows`, `midday`, `midnight`, `oxblood`, `parchment`, `phantom`, `pool`, `rainbowGlitter`, `rush`, `shroomset`, `ski`, `slate`, `snowPaws`, `starburst`, `storybloom`, `sunrise`, `sunset`, `toile`, `twilight`, `watercolor`, `whisky`, `winterWonderland`.

Available effects (default `none`): `none`, `balloons`, `basketball`, `beachballs`, `beerPong`, `bows`, `bubbles`, `bunnies`, `cascade`, `cash`, `christmasLights`, `confetti`, `confettiExplosion`, `crayons`, `dandelions`, `disco`, `doge`, `fireCannons`, `fireflies`, `fireworks`, `foils`, `football`, `gelt`, `ghosts`, `gingerbread`, `ginkgo`, `glowbugs`, `graduation`, `handprints`, `hearts`, `kisses`, `lasers`, `leaves`, `lightning`, `lights`, `magnolias`, `pizzaToppings`, `presents`, `sakura`, `shadowBats`, `shamrock`, `smoke`, `snowflakes`, `snowman`, `spaceInvaders`, `sparkles`, `spiders`, `spiderwebs`, `starrySky`, `stars`, `sunbeams`, `tennis`, `thanksgivingFood`, `winterCreatures`.

### Update Event

```bash
python3 clis/partiful.py update <event_id> \
  --title "New Title" \
  --description "New description" \
  --location "New Location" \
  --date 2026-03-20 --time 01:00 \
  --image /path/to/flyer.png
```

All flags are optional. Only provided fields are updated. Date/time must be provided together and are in UTC. Image uploads the file and links it to the event.

### Get Event

```bash
python3 clis/partiful.py get <event_id>
```

Returns event fields as JSON.

### Delete Event

```bash
python3 clis/partiful.py delete <event_id>
```

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `No auth config found` | Missing `clis/.partiful-auth.json` | Run the auth flow (send-code + login) |
| `HTTP 401` | Expired refresh token | Re-authenticate with send-code + login |
| `HTTP 403` on token refresh | Missing Referer header | Already handled in CLI code |
