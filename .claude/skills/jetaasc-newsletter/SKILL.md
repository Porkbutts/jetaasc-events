---
name: jetaasc-newsletter
description: |
  Create JETAASC (JET Alumni Association of Southern California) monthly newsletter campaigns in Mailchimp.
  Use when user wants to create a newsletter, draft a newsletter, send a monthly update, or mentions JETAASC newsletter.
  Triggers: "create newsletter", "draft newsletter", "monthly newsletter", "send newsletter", "JETAASC update".
---

# JETAASC Newsletter Skill

Create monthly newsletter campaigns for JETAASC using Mailchimp.

## Newsletter Structure

| Section | Required | Content |
|---------|----------|---------|
| Announcements | Yes | Org updates, volunteer calls, leadership news |
| Spotlight | No | Feature a JET alum, community member, or achievement |
| Event Recaps | No | Photos/highlights from recent events |
| Upcoming Events | Yes | Events with: title, flyer image, description, date/time, location (optional: cost, RSVP link) |
| Job Opportunities | No | Job listings relevant to JET alums |

## Workflow

### 1. Gather Content

Ask the user for content for each section:

```
I'll help create the JETAASC newsletter. I need content for:

**Required:**
- Announcements (org updates, calls to action)
- Upcoming Events (for each: title, date/time, location, description, flyer image URL; optional: cost, RSVP link)

**Optional (skip if none this month):**
- Spotlight (member name, JET placement, what they're doing now)
- Event Recaps (event name, highlights, attendance)
- Job Opportunities (title, company, requirements, how to apply)

Also needed:
- Subject line (e.g., "JETAASC February 2026 Newsletter")
- Preview text (short teaser, ~50 chars)
```

### 2. Process Images

When the user provides image URLs (flyers, photos, etc.):

1. **Download the image** using curl:
   ```bash
   curl -L -o /tmp/event-flyer.png "https://example.com/flyer.png"
   ```

2. **Check file size** - Mailchimp limit is 1MB:
   ```bash
   ls -la /tmp/event-flyer.png
   ```

3. **Compress if needed** (if >1MB) using ImageMagick:
   ```bash
   # Resize to max 1200px width and compress quality
   convert /tmp/event-flyer.png -resize 1200x\> -quality 85 /tmp/event-flyer-compressed.jpg
   ```

4. **Upload to Mailchimp** using MCP tool:
   ```
   mailchimp_upload_image(image_path="/tmp/event-flyer-compressed.jpg", name="event-name-flyer.jpg")
   ```

5. **Use returned URL** in the newsletter HTML content

> **Note:** Always download and re-upload images rather than hotlinking external URLs. This ensures images remain available and load reliably for all recipients.

### 3. Build HTML Content

1. Read `assets/template.html`
2. Replace placeholder content in each `mc:edit` section with user's content
3. For upcoming events, use this structure per event:
```html
<div class="event-block">
  <div class="event-date">[SHORT DATE]</div>
  <div class="event-title">[TITLE]</div>
  <div class="event-flyer"><img src="[FLYER_URL]" alt="[TITLE] Flyer"></div>
  <div class="event-description"><p>[DESCRIPTION]</p></div>
  <div class="event-details">
    <p><strong>Date:</strong> [FULL DATE/TIME]</p>
    <p><strong>Location:</strong> [LOCATION]</p>
    <!-- Optional: include only if there's a cost -->
    <p><strong>Cost:</strong> [COST]</p>
  </div>
  <!-- Optional: include only if RSVP link provided -->
  <a href="[RSVP_URL]" class="btn" style="color:#ffffff;">RSVP Here</a>
</div>
```
4. Remove optional sections if user has no content for them

### 4. Create Mailchimp Campaign

Use Mailchimp MCP tools:

1. `mailchimp_create_campaign`:
   - list_id: `27201f5231`
   - subject_line: [from user]
   - preview_text: [from user]
   - from_name: `JETAASC`
   - reply_to: `officers@jetaasc.org`
   - title: `[Month Year] Newsletter`

2. `mailchimp_set_content`:
   - campaign_id: [from above]
   - html: [the built HTML]

### 5. Confirm with User

```
Newsletter draft created!
- Campaign ID: [ID]
- Subject: [SUBJECT]

Would you like me to send a test email? Provide an email address.
```

## Fixed Values

| Field | Value |
|-------|-------|
| Audience ID | `27201f5231` |
| From Name | `JETAASC` |
| Reply-to | `officers@jetaasc.org` |
| Brand Color | `#2baadf` |
| Header Image | `https://gallery.mailchimp.com/c83f204740850ff66ba2d6475/images/87754776-0575-45d3-b40d-e387de4dd6a5.jpg` |

## Resources

- `assets/template.html` - HTML email template with all styling and structure
