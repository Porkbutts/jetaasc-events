# Facebook Publishing

Facebook has no API for creating group events, so this runs as browser automation
against the real Facebook UI using the `claude-in-chrome` tools.

**You fill out the entire form and then stop. Never click "Create event".**
Adrian reviews the filled form in the browser and clicks it himself.

## Group

JETAASC - JET Alumni of Southern California & Arizona (private, ~1.1K members)
Group ID `3273930410`

Go straight to the pre-scoped create dialog rather than clicking through the group:

```
https://www.facebook.com/events/create/?dialog_entry_point=group_events_tab&group_id=3273930410
```

This opens with "Who can see it?" already bound to the JETAASC group.

## Prerequisites

Chrome integration must be connected. If the `mcp__claude-in-chrome__*` tools are
not available, tell Adrian to run `/chrome` and restart Claude Code. Do not fall
back to Playwright; it has a separate browser profile and is not logged into
Facebook.

## Fields

| Field | What to enter |
|-------|---------------|
| Cover photo | The event flyer (see Cover Photo below) |
| Host | Leave as Adrian's personal profile (the default) |
| Event name | Event title |
| Start date / time / timezone | Event start; timezone defaults to PDT |
| End date and time | Click "+ End date and time" and set it if the event has one. If there is no known end time, skip it. |
| In person or virtual | "In person" for venue events, which reveals the location field |
| Add location | Venue name and address (see Location below) |
| Who can see it? | Already set to the JETAASC group. Leave it. |
| Group event privacy | Leave as "Members only" |
| Invite friends who are group members | **Turn on.** Defaults to off. This invites Adrian's friends who are already JETAASC members, which is the reach we want. |
| Details | Description, cost, and RSVP link |
| Add co-hosts / Repeat event | Leave collapsed |

## Description Format

Plain text. Newlines and blank lines work; URLs go in unlinked and Facebook
renders them. Mirror the other platforms:

```
[One or two sentence hook]

What: [Brief description]
When: [Date and time]
Where: [Venue and address]
Cost: [Price or "Free"]

RSVP: [Partiful or Google Form link]
```

## Location

**Prefer a real matched place.** A matched place gives the event a linked venue
with a map and lets attendees see other events there. Free text gives none of
that. Only fall back to free text when the picker genuinely cannot find the venue.

Type the venue name into the location field and read the results. **Judge each
result by the address line underneath the name, not by its position in the list.**
The list is ranked by global check-in count, so a popular same-named business
abroad will outrank a small local one.

Select a result when its address matches the actual venue (the right street, city,
and state). Venues with an established Facebook Page match well: searching
"Japanese American National Museum" returns it as the top hit with
"100 N Central Ave, Los Angeles, CA".

**Fall back to free text when:**

- No result has a plausible Southern California or Arizona address. Small
  independent venues often have no usable Facebook Page. "3CAT Handcrafted
  Beverage" (Tustin) returns only results in the Philippines, Taiwan, and Vietnam;
  "Tea Master Matcha Cafe" returns the Philippines, Belgium, Hong Kong, and Tokyo.
- The results are street addresses rather than businesses. If the venue name starts
  with a digit, the search degrades into address matching: "3CAT Tustin" returns
  "3 Tustin Rd, Pasadena" and similar. Never accept one of these.

Adding the city to the query does not reliably help, so do not burn many attempts
on rephrasing. Try the venue name, maybe once more with the city, then fall back.

To use free text: type the full venue name and address, then pick the last row of
the dropdown, which reads `Just use "<your text>"`. It is pre-checked and accepts
arbitrary text. Scroll the dropdown if it is not visible.

Whatever you type here ships verbatim, so `zoom` on the field and read it back
before selecting the row. See Dropped Characters below.

When you report the filled form for review, say which one you used, so Adrian can
check a matched venue is the right branch.

## Cover Photo

Never click the "Upload" item in the cover photo menu. It opens a native OS file
dialog that Claude cannot see or dismiss, and it freezes the browser session.

Instead:

1. Click the "Edit" button on the cover image, which opens an Upload / Gallery / GIF menu
2. `find` the file input with a query like "file input associated with the Upload option in the event cover photo menu"
3. `file_upload` with that ref and the local flyer path

**Verify you have the right file input.** A generic search for a file input can
return the group's cover photo input from the page underneath. Uploading there
replaces the JETAASC group's cover photo. The correct element is the one tied to
"Edit event cover photo or video". If the description of the ref mentions the
group cover, it is the wrong one.

`file_upload` only accepts files shared with the session. The session scratchpad
directory works. If the flyer is a URL, download it locally first.

Facebook's cover is roughly 16:9 and JETAASC flyers are usually portrait or square,
so expect cropping. Accept the crop for now, but eyeball the result and mention it
to Adrian if something important like the date or RSVP text gets cut off.

## Dates

Typing into the date field updates the visible text without committing the value.
Type the date, press Return, then reopen the picker and confirm the calendar is
showing the right month with the right day highlighted. Skipping the verify step
risks silently publishing the wrong date.

Both entry methods work; typing plus Return is more reliable than clicking calendar
cells across month boundaries.

## Dropped Characters

`computer type` sometimes drops a keystroke, and Facebook accepts the result
silently. A single run of the location field produced "Los Angele" and then, on
the retype, "Los Angels". Nothing errors; the typo just ships.

Short fields are the risk, because a dropped character in a venue or event name is
wrong on the published event. Long prose usually survives, and a typo there is
cosmetic.

Type short fields in chunks rather than one long string, then read the value back
with `zoom` on the field before moving on. The field scrolls horizontally as you
type, so a screenshot may show only the tail; zoom on the whole input.

To fix one missing character, do not retype the field, which tends to drop a
different character. Press `End`, arrow `Left` the exact number of characters that
follow the gap, and type the single character.

## Steps

1. Navigate to the create URL above
2. Upload the flyer as the cover photo
3. Fill start date and time, and end date and time if there is one, verifying the dates committed
4. Set "In person", then search the location and either select a matching place or fall back to free text
5. Turn on "Invite friends who are group members"
6. Fill the details/description
7. Fill the event name **last**
8. Screenshot the completed form and tell Adrian it is ready for review, with a note of anything worth checking (bad flyer crop, ambiguous venue)
9. Stop. Do not click "Create event".

Filling the name last is deliberate: the Create button stays disabled while the
name is empty, so the form cannot be submitted by a stray Return keypress while
you are still working.

## Gotchas

| Symptom | Cause | Fix |
|---------|-------|-----|
| Browser session unresponsive | Native file dialog opened | Adrian must dismiss it manually. Use `file_upload`, never click Upload. |
| Group cover photo changed | Uploaded to the group's file input | Verify the ref belongs to the event dialog before uploading |
| Wrong date on the event | Typed date never committed | Press Return, then reopen the picker to confirm |
| Location resolves to another country | Results rank by global check-ins | Check the address line; if nothing is local, use the `Just use "..."` free text row |
| Results are street addresses, not the venue | Venue name starts with a digit | Do not accept them; fall back to free text |
| Location field missing | "In person" not selected | Set the in person/virtual dropdown first |
| Venue or event name missing a letter | `computer type` dropped a keystroke | `zoom` on the field to read it back; fix with `End`, `Left` xN, and type the one character |
| Tab no longer exists | Adrian closed the tab | Call `tabs_context_mcp` for fresh IDs |
