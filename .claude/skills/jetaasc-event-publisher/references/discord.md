# Discord Publishing

## Server
JETAASC Discord Server

## Guild ID
`1066185009695838268`

## MCP Tool
Use `discord_create_event` from the Discord Events MCP server.

## Handling Flyer URLs
If the flyer is provided as a URL (e.g., Google Drive, Dropbox, direct image link), download it to a temp file first:

```bash
# For direct image URLs:
curl -L -o /tmp/event-flyer.png "https://example.com/image.png"
```

Then pass the local path to `image_path`.

## Required Parameters
| Parameter | Description |
|-----------|-------------|
| `name` | Event title |
| `description` | Event details (include cost and RSVP link) |
| `scheduled_start_time` | ISO8601 timestamp (e.g., `2026-02-15T18:00:00-08:00`) |
| `scheduled_end_time` | ISO8601 timestamp (required for external events) |
| `entity_type` | `EXTERNAL` for in-person events, `VOICE` for voice channel events |
| `location` | Venue address (required for EXTERNAL events) |
| `image_path` | (Optional) Local file path to cover image (PNG, JPG, GIF, WebP) |

## Event Link Format
After creating the event, construct a shareable link:
```
https://discord.com/events/1066185009695838268/{EVENT_ID}
```
The Event ID is returned by `discord_create_event` in the response.

## Example
```
discord_create_event(
  name: "JETAASC Boba Banter",
  description: "Join us for boba!\n\nCost: Free\nRSVP: https://forms.gle/...",
  scheduled_start_time: "2026-02-22T15:00:00-08:00",
  scheduled_end_time: "2026-02-22T17:00:00-08:00",
  entity_type: "EXTERNAL",
  location: "Half & Half Tea Express, Los Angeles",
  image_path: "/path/to/event-flyer.png"
)
```
