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
| Announcements | No | Org updates, volunteer calls, leadership news |
| Event Recap | No | Photos/highlights from recent events |
| Spotlight | No | Feature a JET alum, community member, or achievement |
| Upcoming Events | Yes | Events with: title, flyer image, description, date, time, location (optional: cost, RSVP link) |
| Job Opportunities | Yes | Job listings relevant to JET alums + JETAA Job Board link (always included) |

## Drafting Phase

Most issues are assembled in a Google Doc over the course of a month before any
Mailchimp campaign exists. Board members contribute to that doc directly. During
this phase the doc is the source of truth. **Do not create a campaign until the
user explicitly asks to build it** — "add this event to the newsletter" means the
doc, not Mailchimp.

### 1. The monthly doc

Named `<Month> <Year> Newsletter`, living in the **Officers Shared Drive**
(`0AMaedj5HWQ5YUk9PVA`). It is not in My Drive, so a plain `files list` will not
find it — the query needs the shared-drive params:

```bash
gws drive files list --params '{"q":"trashed=false and name contains '"'"'Newsletter'"'"'","corpora":"drive","driveId":"0AMaedj5HWQ5YUk9PVA","includeItemsFromAllDrives":true,"supportsAllDrives":true,"orderBy":"modifiedTime desc","fields":"files(id,name,modifiedTime)"}'
```

If the doc for the target month does not exist, create it in that shared drive
with the standard skeleton: the two cadence lines at top, then the five fixed H1
headings in order.

```
Submission deadline: 2nd Friday of the preceding month
Sending deadline: 3rd Friday of the preceding month
```

| H1 heading | Notes |
|---|---|
| Announcements | Org updates, volunteer calls, leadership news |
| Event Recap | Recent events worth writing up |
| Alumni Spotlight | Featured alum |
| Events | One H2 per event |
| Job Opportunities | Listings + the standing JETAA Job Board link |

Older issues are named `<Month> <Year> Outline and Formatting`; same purpose.

### 2. Placeholders are normal

Empty headings and `[PLACEHOLDER: date, time, and venue TBD]` notes are expected
mid-cycle and mean the issue is **not** ready to build. When the user asks to add
something that is not fully pinned down, write the placeholder rather than
inventing details. Never fill a gap with a plausible-sounding date or venue.

Each event under `Events` should reach these fields before build:

- Title (H2)
- Description
- Date and time
- Venue and address
- Cost, if any
- RSVP link, if any
- Flyer link (see below)

### 3. Images in the doc

**Images are embedded directly in the doc**, each one placed under the item it
belongs to: the mascot banner at the top under the `<Month> Newsletter` line with
its credit line beneath, and each event's flyer under that event's details. The
doc is meant to be a complete build input — if an image is missing from it, the
build is not one-shot.

#### Reading a doc that has images

`docs.documents.get` returns embedded images as `inlineObject` references with a
`contentUri` that cannot be fetched. **Images are invisible on that path** — this
is why reading a doc appears to show no images at all. Do not use it alone when
the doc may contain images.

Export the doc as a zip instead. It returns the HTML plus an `images/` directory
holding the real bytes, and the HTML preserves each image's position, so images
can be matched to the section they sit under:

```bash
gws drive files export --params '{"fileId":"DOC_ID","mimeType":"application/zip"}' -o doc.zip
unzip -q doc.zip -d doc/ && ls doc/images/
```

Read the HTML for the outline and the `<img src="images/...">` positions together,
so each image is tied to the heading it falls under. Use `documents.get` only when
the text alone is needed.

#### Writing images into a doc

`insertInlineImage` requires a **publicly reachable URL** — local bytes cannot be
inserted directly. Upload the file to Public Flyers (below), give it
`anyone:reader`, then insert by URL:

```
https://drive.google.com/uc?export=download&id=FILE_ID
```

Set `objectSize` to a sane display width (banner ~468 PT, portrait flyers ~240 PT)
or the image renders at full size in the doc.

To place an image on its own line under an existing paragraph, do it in two
batches: first insert `\n` plus a unique marker string, then re-fetch, and in a
second batch delete the marker range and insert the image at that index. Process
anchors in **descending index order** so earlier offsets stay valid.

#### The ~2000px cap

Docs stores an embedded image unchanged if both edges are within roughly 2000px,
and scales down and re-encodes anything larger. Measured:

| in | out |
|---|---|
| 1400×613 | identical bytes |
| 1545×2000, 2.3 MB | identical bytes |
| 1536×2048 | 1500×1999, re-encoded |
| 3900×1708 | 1999×876, re-encoded |

Size in bytes does not trigger it; only dimensions. Export is always a faithful
read of whatever Docs stored, so any loss happened at insert time.

This is harmless for email, where the banner is resized to 1400px anyway and
flyers display a few hundred pixels wide. It matters only for print or
large-format social use, which is why originals still belong in Public Flyers.

#### Public Flyers

Full-resolution originals live in **Public Flyers**
(`1C7glPr2Oaw-h8sdFDAIu2vbPt_MT6yJu`) in the Officers Shared Drive. The doc copy
serves the newsletter; this folder serves Discord, Wix, Partiful, and print, and
is the source URL for embedding.

- Name flyers `JETAASC_<YYYY-MM-DD>_<Event_Name>.<ext>`.
- Name banners `<mon><year>-banner-reuben-barrientes.jpg`, resized to 1400px wide
  (`sips -Z 1400 in.jpg --out out.jpg -s format jpeg -s formatOptions 88`).
- Every file needs an explicit `anyone:reader`.
- Keep a `Flyer: <link>` line under the embedded image pointing at the original,
  so the full-resolution copy is reachable from the doc.

Three Drive gotchas, all hit in practice:

- **`gws drive +upload --parent` 404s on shared drive folders** — the helper does
  not pass `supportsAllDrives`. Upload to My Drive, then move the file in.
- **Folders cannot be moved into a shared drive via the API** (403
  `teamDrivesFolderMoveInNotSupported`). Files can. Move a folder by dragging it
  in the Drive web UI, or recreate it and move the files.
- **Moving a file into a shared drive silently strips `anyone:reader`**, leaving
  only member roles. Always re-add it afterward and verify:

```bash
gws drive permissions create --params '{"fileId":"FILE_ID","supportsAllDrives":true}' --json '{"type":"anyone","role":"reader"}'
```

File IDs survive a move, so existing links keep working once sharing is restored.

### 4. Handing off to the build

The goal is that the user can say **"make the newsletter from this doc"** and
nothing else. When given a doc:

1. Export it as a zip (above) so text and images arrive together.
2. Map each image to the section it sits under. The banner is the image above the
   first `<h1>`; a flyer is the image inside an event's block.
3. List anything still empty or still marked `[PLACEHOLDER: ...]`, and ask whether
   to drop those sections or wait. Do not invent missing details.
4. Continue to Gather Content below with doc text and extracted images in hand.

The images pulled from the zip are ready to use — resize the banner to 1400px if
it is larger, then upload to Mailchimp per Process Images.

Short issues are often dictated straight into the terminal instead. Do not
require a doc; take content from wherever the user offers it.

## Workflow

### 1. Gather Content

If a monthly doc exists, start from it (see Drafting Phase above). Otherwise ask
the user for content for each section:

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

### 2. Process Images

Images come from three places: extracted from the monthly doc's zip export (see
Drafting Phase), a local path, or a URL. In every case:

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

### 3. Draft Content in Markdown

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

### 4. Build and Publish via Subagent

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

### 5. Share Preview

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
