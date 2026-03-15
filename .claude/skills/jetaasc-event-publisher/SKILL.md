---
name: jetaasc-event-publisher
description: Publish JETAASC (JET Alumni Association of Southern California) events to multiple platforms. Use when user wants to publish an event, draft an event, create event descriptions, or share events to Wix blog, Google Calendar, Discord, or Facebook. Triggers include "publish event", "draft event", "create event post", "share to wix/calendar/discord/fb", or any JETAASC event-related publishing task.
---

# JETAASC Event Publisher

Publish JETAASC events to multiple platforms: Wix Blog, Google Calendar, Discord, and Facebook.

## Workflow

### 1. Collect Event Information

Gather from user:
- **Title**: Event name
- **Date/Time**: Start (and end if applicable)
- **Location**: Venue name and address
- **Description**: What the event is about
- **Cost**: Price (optional, include member/non-member pricing if applicable)
- **RSVP Link**: Google Form link (optional)
- **Flyer/Image**: Event artwork URL or local file path

**Handling Flyer Images:**

The flyer must be a publicly accessible URL for Wix import. Resolve the image based on what the user provides:

1. **Local file path** (e.g., `~/Downloads/flyer.png`):
   - Upload to Google Drive `Public Flyers` folder (ID: `1ptC7GpyjuHmwhTTAed1Y7GmuLGY1b-XR`) using `gdrive_upload_file`
   - The folder has public "anyone with link" view permissions, so the file inherits it
   - Convert the returned file ID to a direct download URL: `https://drive.google.com/uc?export=download&id=FILE_ID`
   - For Discord, use the original local file path directly (it accepts local paths)

2. **Google Drive share link** (e.g., `https://drive.google.com/file/d/FILE_ID/view`):
   - Convert to direct download URL: `https://drive.google.com/uc?export=download&id=FILE_ID`

3. **Direct image URL** (e.g., `https://example.com/flyer.png`):
   - Use as-is

### 2. Confirm Details and Select Platforms

Display a summary of the event details for user confirmation.

Then ask two questions using `AskUserQuestion`:

**Question 1 (multiSelect: true):** "Which platforms do you want to publish to?"
- Wix Blog
- Discord
- Google Calendar
- Facebook

**Question 2:** "How should I publish to the selected platforms?"
- In parallel (Recommended) - Publish to all platforms simultaneously
- Sequential - Publish one at a time, confirming each before proceeding

### 3. Publish to Selected Platforms

Execute publishing based on user selections. If parallel, launch all platform tasks simultaneously. If sequential, complete each platform before moving to the next.

---

## Platform Details

### Wix Blog

Use Wix MCP tools. See [references/platforms.md](references/platforms.md) for site ID, API endpoints, category/tag IDs. See [references/wix-blog-format.md](references/wix-blog-format.md) for Ricos JSON structure.

Steps:
1. Upload flyer to Wix Media Manager (Import File endpoint)
2. Select appropriate tags by analyzing event title, description, and location
3. Create draft post with title, image, richContent, category, and tags
4. Share draft preview link for user confirmation
5. If user has feedback, update draft via PATCH endpoint. Repeat until approved.
6. On approval, publish draft
7. Return published post URL

### Google Calendar

Create Google Calendar event using `gcal_create_event` MCP tool. See [references/platforms.md](references/platforms.md) for parameters.

### Discord

Create Discord scheduled event using `discord_create_event` MCP tool. See [references/platforms.md](references/platforms.md) for parameters.

After creating the event, construct and return the event link using this format:
```
https://discord.com/events/{GUILD_ID}/{EVENT_ID}
```
The Guild ID is `1066185009695838268` (from Discord MCP config). The Event ID is returned by `discord_create_event`.

### Facebook (Manual)

Provide formatted content for manual posting. See [references/platforms.md](references/platforms.md) for format.

## Quick Reference

| Platform | Method | Status |
|----------|--------|--------|
| Wix Blog | Wix MCP | Ready |
| Discord | Discord MCP | Ready |
| Google Calendar | Google Calendar MCP | Ready |
| Facebook | Manual | Copy/paste |
