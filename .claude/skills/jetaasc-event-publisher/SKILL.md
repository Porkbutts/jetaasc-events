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
- **Flyer/Image**: Event artwork URL or file

**Handling Google Drive URLs:** If the user provides a Google Drive share link (e.g., `https://drive.google.com/file/d/FILE_ID/view`), convert it to a direct download URL for platforms that need to download the image (Wix, Discord):
```
https://drive.google.com/uc?export=download&id=FILE_ID
```

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

Add event to JETAASC Public Calendar. See [references/platforms.md](references/platforms.md) for API details.

Required: Google Calendar API credentials configured.

### Discord

Create Discord scheduled event using `discord_create_event` MCP tool. See [references/platforms.md](references/platforms.md) for parameters.

### Facebook (Manual)

Provide formatted content for manual posting. See [references/platforms.md](references/platforms.md) for format.

## Quick Reference

| Platform | Method | Status |
|----------|--------|--------|
| Wix Blog | Wix MCP | Ready |
| Google Calendar | API | Requires setup |
| Discord | Discord MCP | Ready |
| Facebook | Manual | Copy/paste |
