---
name: jetaasc-newsletter
description: |
  Build and send the JETAASC (JET Alumni Association of Southern California) monthly newsletter campaign in Mailchimp.
  Use when the user is ready to build the actual email: "build the newsletter", "make the newsletter from this doc",
  "create the campaign", "send the newsletter", "send a test".
  To collect or edit content in the monthly Google Doc first, use jetaasc-newsletter-draft instead.
---

# JETAASC Newsletter Skill

Create monthly newsletter campaigns for JETAASC using Mailchimp.

## Newsletter Structure

| Section | Required | Content |
|---------|----------|---------|
| Announcements | No | Org updates, volunteer calls, leadership news |
| Event Recap | No | Photos/highlights from recent events |
| Spotlight | No | Feature a JET alum, community member, or achievement |
| Upcoming Events | Yes | Events with: title, flyer image, description, date, time, location (optional: cost, RSVP link) |
| Job Opportunities | Yes | Job listings relevant to JET alums + JETAA Job Board link (always included) |

## Workflow

### 1. Gather Content

Content usually comes from the monthly Google Doc, which is owned by the
`jetaasc-newsletter-draft` skill. If the user points at one, read it per
**Reading a doc** below. Short issues are often dictated straight into the
terminal instead — don't require a doc.

Otherwise ask the user for content for each section:

```
I'll help create the JETAASC newsletter. I need content for:

**Required:**
- Upcoming Events (for each: title, date, time, location, description, flyer image; optional: cost, RSVP link)

**Optional (skip if none this month):**
- Announcements (org updates, calls to action)
- Event Recaps (event name, highlights, photos)
- Spotlight (member name, JET placement, what they're doing now)
- Job Opportunities (title, company, requirements, how to apply)

Also needed:
- Subject line (e.g., "JETAASC March 2026 Newsletter")
- Preview text (short teaser, ~50 chars)
```

### 2. Reading a doc

`docs.documents.get` silently drops embedded images — it returns them as
`inlineObject` references with a `contentUri` that can't be fetched. Export the
doc as a zip instead, which returns the HTML plus the real image bytes with each
image's position preserved:

```bash
gws drive files export --params '{"fileId":"DOC_ID","mimeType":"application/zip"}' -o doc.zip
unzip -q doc.zip -d doc/
```

The banner is the image above the first `<h1>`; a flyer is the image inside an
event's block. Flag any section still empty or marked `[PLACEHOLDER: ...]` before
building, rather than shipping it.

### 3. Process Images

When you have image files (from a doc export, a local path, or a URL):

1. **Check file size** - Mailchimp limit is 1MB
2. **Compress if needed** (if >1MB) using sips or ImageMagick:
   ```bash
   sips -Z 1200 /path/to/image.png --out /tmp/compressed.jpg -s format jpeg -s formatOptions 85
   ```
3. **Upload to Mailchimp** using MCP tool:
   ```
   mailchimp_upload_image(image_path="/tmp/compressed.jpg", name="descriptive-name.jpg")
   ```
4. **Save the returned URL** for use in the structured content

> **Note:** Always download and re-upload images rather than hotlinking external URLs.

### 4. Draft Content in Markdown

Before building, draft the full newsletter content in markdown and present it to the user for review. This includes the rewritten/polished text for every section — not just a summary of what's included. The user must approve the actual content before the HTML is built.

```
Here's the newsletter draft for your review:

**Campaign Details:**
- Subject: [SUBJECT LINE]
- Preview: [PREVIEW TEXT]

---

[Full markdown content for each section: announcements, event recaps, events, jobs, etc.]

---

Does this look right, or would you like any changes?
```

Only proceed to the build step after the user approves.

### 5. Build and Publish via Subagent

Launch the `newsletter-builder` agent (subagent_type: "general-purpose") with structured content.

**For a new campaign:**
```
Create the Mailchimp campaign with these details:

Subject: [subject line]
Preview: [preview text]
Title: [Month Year] Newsletter
Greeting: [greeting text]

TOC (use nested bullets for sub-items like individual event titles, announcement topics, etc.):
- [section 1]
  - [sub-item]
- [section 2]
  - [sub-item]
...

Sections:

## [Section Name]
[structured content per section type - see agent docs]
...
```

**To update an existing campaign:**
```
Update Mailchimp campaign cc67c2e105 with these details:

[same structured content format as above, omit Subject/Preview/Title if unchanged]

Sections:
...
```

The agent reads the HTML template, interpolates content, and calls Mailchimp APIs. It returns the campaign ID and archive URL.

### 6. Share Preview

After the agent returns, share the archive URL so the user can preview:

```
Newsletter draft ready!
- Campaign ID: [ID]
- Preview: [ARCHIVE URL]

Would you like any changes? I can also send a test email to board@jetaasc.org for review.
```

If the user wants a test email, use `mailchimp_send_test` with the campaign ID and `test_emails: ["board@jetaasc.org"]`.

If changes are needed, launch the agent again with the updated content and the existing campaign_id.

## Fixed Values

| Field | Value |
|-------|-------|
| Audience ID | `27201f5231` |
| From Name | `JETAASC` |
| Reply-to | `officers@jetaasc.org` |
| Brand Color | `#b22222` |
| Header Image | `https://gallery.mailchimp.com/c83f204740850ff66ba2d6475/images/87754776-0575-45d3-b40d-e387de4dd6a5.jpg` |

## Resources

- `assets/template.html` - HTML email template with all styling and structure
- `.claude/agents/newsletter-builder.md` - Subagent that handles HTML building and Mailchimp API calls
