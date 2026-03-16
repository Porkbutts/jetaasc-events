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
- **RSVP Link**: Partiful or Google Form link (optional — see below)
- **Flyer/Image**: Event artwork URL or local file path

**Handling Flyer Images:**

The flyer must be a publicly accessible URL for Wix import. Resolve the image based on what the user provides:

1. **Local file path** (e.g., `~/Downloads/flyer.png`):
   - Upload to Google Drive `Public Flyers` folder (ID: `1ptC7GpyjuHmwhTTAed1Y7GmuLGY1b-XR`) using the `/gws-drive-upload` skill
   - The folder has public "anyone with link" view permissions, so the file inherits it
   - Convert the returned file ID to a direct download URL: `https://drive.google.com/uc?export=download&id=FILE_ID`
   - For Discord, use the original local file path directly (it accepts local paths)

2. **Google Drive share link** (e.g., `https://drive.google.com/file/d/FILE_ID/view`):
   - Convert to direct download URL: `https://drive.google.com/uc?export=download&id=FILE_ID`

3. **Direct image URL** (e.g., `https://example.com/flyer.png`):
   - Use as-is

### 2. RSVP Link

If the user did not provide an RSVP link and one cannot be extracted from the event description or flyer:

Ask the user: "No RSVP link provided. Would you like me to create an RSVP page?"
- **Partiful** (recommended) — creates a public RSVP page with event details. Read the `partiful` skill (`.claude/skills/partiful/SKILL.md`) for CLI reference and command syntax. Pass the event details you already collected — do not re-ask the user.
- **Google Form** — use when you need custom fields (e.g., dietary restrictions, T-shirt sizes). Read [references/google-form-rsvp.md](references/google-form-rsvp.md) for the full creation workflow.
- **Skip** — no RSVP needed

### 3. Confirm Details and Select Platforms

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

### 4. Publish to Selected Platforms

Execute publishing based on user selections. If parallel, launch all platform tasks simultaneously. If sequential, complete each platform before moving to the next.

Read the reference doc for each selected platform before publishing:

| Platform | Reference | Method |
|----------|-----------|--------|
| Wix Blog | [references/wix-blog.md](references/wix-blog.md) | Wix MCP |
| Google Calendar | [references/google-calendar.md](references/google-calendar.md) | GWS CLI (`/gws-calendar-insert`) |
| Discord | [references/discord.md](references/discord.md) | Discord MCP |
| Facebook | [references/facebook.md](references/facebook.md) | Manual (copy/paste) |
