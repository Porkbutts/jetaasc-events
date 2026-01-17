# Platform Publishing Reference

## Wix Blog

### API Endpoints

**Create Draft:**
```
POST https://www.wixapis.com/blog/v3/draft-posts
```

**Update Draft:**
```
PATCH https://www.wixapis.com/blog/v3/draft-posts/{draftPostId}
Body: {"draftPost": {"id": "{draftPostId}", "richContent": {...}}}
```
Use this to apply user feedback/changes before publishing.

**Publish Draft:**
```
POST https://www.wixapis.com/blog/v3/draft-posts/{draftPostId}/publish
```

### Draft Preview Link
After creating a draft, share this link for review:
```
https://manage.wix.com/dashboard/68b9accd-a629-4996-a8e3-bb4a7ed9a186/blog/{draftPostId}/edit
```

### Site ID
`68b9accd-a629-4996-a8e3-bb4a7ed9a186`

### Category ID for "Upcoming"
`b2dba553-f903-4dd8-859a-94afe80730e3`

### Common Tags
| Tag | ID |
|-----|-----|
| shinnenkai | a93eb3fa-3212-4058-abca-9168f0e9de6f |
| bonenkai | 6b7de19c-0aed-477c-80b2-48a2ff277f0d |
| networking | f06e35c4-925c-4049-9a36-822f3175e952 |
| Japanese | a257ee18-8ee3-44e5-83e3-5b72995c7ffb |
| los angeles | 8787c4f7-f690-4785-9382-fd8b89439a34 |
| orange county | bd21c0d1-659e-40c4-9d12-663b11a5c489 |
| san diego | e058cb3c-3073-4b67-8434-3713167e939e |
| little tokyo | e5adf867-9283-4d80-8b08-a52ef97c3f75 |
| karaoke | 8098c398-8293-46f2-b365-e4019223c64e |
| movie night | 5f49e036-7f64-4714-950c-857ab3f5aa0d |
| natsukashii-kai | bcad48d3-a0a9-4e18-bd3d-7181af411a6d |
| nihongo dake dinner | 0c38eb38-27e2-475c-999f-dd01291a5434 |
| boba banter | 4e6e89fd-adb1-48e6-bc2a-dba8e34155c3 |
| welcome back | 91b5fce7-7329-4332-a776-5521fca53b12 |
| online event | 36942460-f118-4126-9ba0-59bed75c4db8 |
| virtual | 82463a96-f9da-4061-b0a1-cffdc0f03cea |

### Creating New Tags
If the event needs a tag that doesn't exist, create it first:
```
POST https://www.wixapis.com/blog/v3/tags
Body: {"tag": {"label": "new tag name", "language": "en"}}
```
The response includes the new tag's `id` to use in the blog post's `tagIds` array.

### Listing All Tags
To find existing tags or check if a tag exists:
```
GET https://www.wixapis.com/blog/v3/tags
```

### Uploading Images
Before creating a blog post, upload the event flyer to Wix Media Manager:
```
POST https://www.wixapis.com/site-media/v1/files/import
Body: {"url": "<image-url>", "displayName": "<filename>.png", "mimeType": "image/png"}
```
Use the returned `file.id` in the blog post.

---

## Google Calendar

### Calendar
JETAASC Public Calendar

### API Setup Required
1. Create a Google Cloud project
2. Enable Google Calendar API
3. Create OAuth 2.0 credentials or service account
4. Share JETAASC Public Calendar with the service account email

### API Endpoint
```
POST https://www.googleapis.com/calendar/v3/calendars/{calendarId}/events
```

### Event Object Structure
```json
{
  "summary": "Event Title",
  "location": "Venue Address",
  "description": "Event details and RSVP link",
  "start": {
    "dateTime": "2026-02-15T18:00:00-08:00",
    "timeZone": "America/Los_Angeles"
  },
  "end": {
    "dateTime": "2026-02-15T21:00:00-08:00",
    "timeZone": "America/Los_Angeles"
  }
}
```

---

## Discord

### Server
JETAASC Discord Server

### MCP Tool
Use `discord_create_event` from the Discord Events MCP server.

### Handling Flyer URLs
If the flyer is provided as a URL (e.g., Google Drive, Dropbox, direct image link), download it to a temp file first:

```bash
# For direct image URLs:
curl -L -o /tmp/event-flyer.png "https://example.com/image.png"
```

Then pass the local path to `image_path`.

### Required Parameters
| Parameter | Description |
|-----------|-------------|
| `name` | Event title |
| `description` | Event details (include cost and RSVP link) |
| `scheduled_start_time` | ISO8601 timestamp (e.g., `2026-02-15T18:00:00-08:00`) |
| `scheduled_end_time` | ISO8601 timestamp (required for external events) |
| `entity_type` | `EXTERNAL` for in-person events, `VOICE` for voice channel events |
| `location` | Venue address (required for EXTERNAL events) |
| `image_path` | (Optional) Local file path to cover image (PNG, JPG, GIF, WebP) |

### Example
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

---

## Facebook (Manual)

Facebook Events cannot be created via API for personal/group pages. Create manually at https://www.facebook.com/events/create

### Required Information
- **Event Name**: Event title
- **Start Date/Time**: Event start
- **End Date/Time**: Event end (optional)
- **Location**: Venue name and address
- **Description**: Event details with RSVP link
- **Cover Photo**: Upload event flyer

### Suggested Description Format
```
[Event description]

What: [Brief description]
When: [Date and time]
Where: [Location/Address]
Cost: [Price or "Free"]

RSVP: [Google Form link]
```
