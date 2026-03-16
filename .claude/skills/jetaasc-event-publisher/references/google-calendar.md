# Google Calendar Publishing

## Calendar
JETAASC Public Calendar

## Calendar ID
`jetaasc.org_hjd9mjsdhqrniqbfup80ctf9pc@group.calendar.google.com`

## Tool
Use the `/gws-calendar-insert` skill.

## Required Parameters
| Flag | Description |
|------|-------------|
| `--calendar` | Calendar ID (use JETAASC Public Calendar ID above) |
| `--summary` | Event title |
| `--start` | ISO8601 timestamp (e.g., `2026-02-15T18:00:00-08:00`) |
| `--end` | ISO8601 timestamp |
| `--location` | Venue address |
| `--description` | Event details (include cost and RSVP link) |

## Example
```bash
gws calendar +insert \
  --calendar 'jetaasc.org_hjd9mjsdhqrniqbfup80ctf9pc@group.calendar.google.com' \
  --summary 'JETAASC Boba Banter' \
  --description 'Join us for boba!\n\nCost: Free\nRSVP: https://forms.gle/...' \
  --location 'Half & Half Tea Express, Los Angeles' \
  --start '2026-02-22T15:00:00-08:00' \
  --end '2026-02-22T17:00:00-08:00'
```
