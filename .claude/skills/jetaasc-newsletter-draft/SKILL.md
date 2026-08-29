---
name: jetaasc-newsletter-draft
description: |
  Collect and edit JETAASC newsletter content in the monthly Google Doc, before any Mailchimp campaign exists.
  Use when the user wants to add, change, or check on newsletter content: adding an event or announcement to
  an upcoming issue, starting a new month's doc, dropping in a flyer, or asking what is still missing.
  Triggers: "add X to the newsletter", "put this in the September newsletter", "start the October newsletter",
  "what's in the newsletter so far", "is the newsletter ready", "add this flyer to the newsletter".
  For building or sending the actual email, use jetaasc-newsletter instead.
---

# JETAASC Newsletter Draft

Owns the monthly Google Doc: the place newsletter content is gathered over the
course of a month, before any Mailchimp campaign exists.

**This skill never touches Mailchimp.** "Add this event to the newsletter" means
the doc. Building the campaign is `jetaasc-newsletter`, and only when the user
explicitly asks to build or send.

The goal is that the doc ends up complete enough that the build is one shot:
every section filled or deliberately empty, every image present. If an image is
missing from the doc, the build is not one-shot.

## The monthly doc

Named `<Month> <Year> Newsletter`, in the **Officers Shared Drive**
(`0AMaedj5HWQ5YUk9PVA`). It is not in My Drive, so a plain `files list` will not
find it — the query needs the shared-drive params:

```bash
gws drive files list --params '{"q":"trashed=false and name contains '"'"'Newsletter'"'"'","corpora":"drive","driveId":"0AMaedj5HWQ5YUk9PVA","includeItemsFromAllDrives":true,"supportsAllDrives":true,"orderBy":"modifiedTime desc","fields":"files(id,name,modifiedTime)"}'
```

Older issues are named `<Month> <Year> Outline and Formatting`; same purpose.

### Creating a month's doc

If the doc for the target month does not exist, create it in that shared drive
with the cadence lines at top, then the five H1 headings in order and nothing
else. Board members fill in the rest.

```
Submission deadline: 2nd Friday of the preceding month
Sending deadline: 3rd Friday of the preceding month
```

| H1 heading | Holds |
|---|---|
| Announcements | Org updates, volunteer calls, leadership news |
| Event Recap | Recent events worth writing up |
| Alumni Spotlight | Featured alum |
| Events | One H2 per event |
| Job Opportunities | Listings, plus the standing JETAA Job Board link |

Note that the cadence runs a month ahead of the issue name: the September issue
is due and sent during August.

## Adding content

Match the surrounding voice: friendly, inclusive, concise, skimmable. No em
dashes. Write the copy as it should appear in the email, not as notes.

Each event under `Events` needs all of these before the issue can be built:

- Title (H2)
- Description
- Date and time
- Venue and address
- Cost, if any
- RSVP link, if any
- Flyer, embedded (see below)

## Placeholders are normal

Empty headings and `[PLACEHOLDER: ...]` notes are expected mid-cycle and mean
the issue is **not** ready to build. They are information, not a defect.

When asked to add something that is not fully pinned down, write the placeholder
and say what is missing. **Never fill a gap with a plausible-sounding date,
venue, or price.** A wrong date in a doc becomes a wrong date in an email to the
whole chapter.

```
[PLACEHOLDER: date, time, and venue TBD. Tahirah is still finalizing details.]
```

Name who is on the hook when it is known.

## Images go in the doc

Images are embedded directly in the doc, each under the item it belongs to:

- **Mascot banner** at the top, under the `<Month> Newsletter` line, with its
  credit line directly beneath it. This is the asset most likely to be
  forgotten, because it arrives from the artist separately.
- **Event flyers** under that event's details.
- A `Flyer: <link>` line under each embedded image, pointing at the
  full-resolution original.

Storage, naming, permissions, URL forms, and the ~2000px cap are all in
[../../references/public-flyers.md](../../references/public-flyers.md). Read it
before uploading or embedding anything.

### Embedding an image

`insertInlineImage` requires a **publicly reachable URL** — local bytes cannot
be inserted directly. Upload to Public Flyers, confirm `anyone:reader`, then
insert using the `uc?export=download&id=FILE_ID` form.

Set `objectSize` or the image renders at full size in the doc: banner ~468 PT
wide, portrait flyers ~240 PT.

To place an image on its own line under an existing paragraph, use two batches.
Google Docs indices shift as content is inserted, so a single batch that both
locates and fills positions will land in the wrong place.

1. Insert `\n` plus a unique marker string (e.g. `«BANNER»`) at each anchor.
2. Re-fetch the document, find each marker's paragraph, and in a second batch
   delete the marker range and insert the image at that index.

Process anchors in **descending index order** in both passes, so earlier offsets
stay valid as later ones change.

## Checking the state of an issue

When asked what is in the newsletter or whether it is ready, read the doc and
report honestly:

- Which sections have content
- Which are empty
- Which events are missing required fields
- Whether the banner is present
- How the current date sits against the submission and sending deadlines

Reading text alone is enough for a status check, so `docs.documents.get` is
fine here. It does **not** return embedded images, so to confirm an image is
actually present, export the doc as a zip — see `jetaasc-newsletter`.

## Handing off

When the doc is ready and the user asks to build or send, that is
`jetaasc-newsletter`. Do not create a campaign from this skill.
