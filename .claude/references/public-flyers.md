# Public Flyers and image handling

Shared reference. Read this before uploading, linking, or embedding any JETAASC
flyer or banner. Three skills depend on it: `jetaasc-event-publisher`,
`jetaasc-newsletter-draft`, and `jetaasc-newsletter`.

## Where flyers live

Full-resolution originals live in **Public Flyers**
(`1C7glPr2Oaw-h8sdFDAIu2vbPt_MT6yJu`) in the **Officers Shared Drive**
(`0AMaedj5HWQ5YUk9PVA`).

The folder serves every channel that needs a stable public image URL: Wix,
Discord, Partiful, Facebook, and the newsletter. It is the source URL when
embedding an image into a Google Doc.

## Naming

| Kind | Pattern | Example |
|---|---|---|
| Event flyer | `JETAASC_<YYYY-MM-DD>_<Event_Name>.<ext>` | `JETAASC_2026-10-08_Returnees_Welcome_Reception_AZ.png` |
| Newsletter banner | `<mon><year>-banner-reuben-barrientes.jpg` | `sep2026-banner-reuben-barrientes.jpg` |

## Permissions

Every file needs an explicit `anyone:reader`. Files do **not** reliably inherit
it from the folder, and without it Wix and Discord imports fail silently.

```bash
gws drive permissions create --params '{"fileId":"FILE_ID","supportsAllDrives":true}' --json '{"type":"anyone","role":"reader"}'
```

Verify after every upload or move, rather than assuming.

## Direct image URLs

Different consumers want different URL forms for the same file:

| Use | URL form |
|---|---|
| Wix import, any server-side fetch | `https://lh3.googleusercontent.com/d/FILE_ID` |
| Embedding into a Google Doc | `https://drive.google.com/uc?export=download&id=FILE_ID` |
| Human-readable link in a doc | `https://drive.google.com/file/d/FILE_ID/view` |
| Discord, Facebook | the original local file path |

The `uc?export=download` form redirects through an HTML page and can fail for
server-side importers like Wix, which is why Wix gets the `lh3` form.

## Drive gotchas

All three were hit in practice; none of them announce themselves.

- **`gws drive +upload --parent` 404s on shared drive folders.** The helper does
  not pass `supportsAllDrives`. Upload to My Drive first, then move the file in.
- **Folders cannot be moved into a shared drive via the API** (403
  `teamDrivesFolderMoveInNotSupported`). Files can. Move a folder by dragging it
  in the Drive web UI, or recreate the folder and move the files individually.
- **Moving a file into a shared drive silently strips `anyone:reader`,** leaving
  only shared-drive member roles. Re-add it after every move. File IDs survive a
  move, so existing links keep working once sharing is restored.

## The ~2000px cap on images inside Google Docs

Docs stores an embedded image unchanged when both edges are within roughly
2000px, and scales down and re-encodes anything larger. Measured:

| in | out |
|---|---|
| 1400×613 | identical bytes |
| 1545×2000, 2.3 MB | identical bytes |
| 1536×2048 | 1500×1999, re-encoded |
| 3900×1708 | 1999×876, re-encoded |

Dimensions trigger it, not file size — a 2.3 MB PNG passed through untouched.
Exporting a doc is always a faithful read of whatever Docs stored, so any loss
happened at insert time.

This is harmless for email, where a banner is resized to 1400px anyway and
flyers display a few hundred pixels wide. It matters for print or large-format
social use, which is why the full-resolution original stays in Public Flyers
rather than living only inside a doc.

## Sizing for Mailchimp

Mailchimp's file manager caps uploads at 1 MB.

```bash
sips -Z 1400 in.jpg --out out.jpg -s format jpeg -s formatOptions 88   # banner
sips -Z 1200 in.png --out out.jpg -s format jpeg -s formatOptions 85   # oversized flyer
```
