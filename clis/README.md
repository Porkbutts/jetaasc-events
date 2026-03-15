# partiful-cli

Unofficial CLI for [Partiful](https://partiful.com) event management. No dependencies beyond Python 3 stdlib.

## Auth

**Interactive** (human in terminal):
```sh
python partiful.py login 8185551234
# Sends SMS, prompts for code, saves auth
```

**Non-interactive** (two steps):
```sh
python partiful.py send-code 8185551234
# wait for SMS...
python partiful.py login 8185551234 --code 123456
```

Auth is saved to `.partiful-auth.json` (gitignored). The refresh token auto-renews on each command.

## Commands

### Create event
```sh
python partiful.py create \
  --title "Game Night" \
  --date 2026-04-01 \
  --time 03:00 \
  --description "Bring your own games" \
  --location "123 Main St" \
  --theme champagne \
  --image /path/to/flyer.png
```
Times are in UTC. Returns event ID and URL.

### Update event
```sh
python partiful.py update <event_id> \
  --title "New Title" \
  --description "Updated description" \
  --location "New Location" \
  --date 2026-04-02 --time 04:00 \
  --image /path/to/flyer.png
```

### Get event
```sh
python partiful.py get <event_id>
```

### Delete event
```sh
python partiful.py delete <event_id>
```

## How it works

- **Create** uses `POST api.partiful.com/createEvent`
- **Image upload** uses `POST api.partiful.com/uploadPhoto?uploadType=event_poster` (multipart/form-data)
- **Update/Delete/Get** use the Firestore REST API directly (`firestore.googleapis.com`)
- Auth is Firebase (phone + SMS code -> custom token -> JWT + refresh token)

## Phone number format

Accepts `8185551234` (assumes US +1) or `+18185551234`.
