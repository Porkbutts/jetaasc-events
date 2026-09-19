---
name: jetaasc-canva-flyer
description: Create a JETAASC (JET Alumni Association of Southern California) event flyer in Canva by driving the Chrome browser with Claude in Chrome. Use when the user wants a flyer, graphic, or image for an event to share on socials, the newsletter, Discord, or Facebook. Triggers include "make a flyer", "canva flyer", "create a flyer for", "design a graphic for the event", or any request for event artwork. Produces a saved Canva design and a downloaded PNG.
---

# JETAASC Canva Flyer

Build an event flyer in Canva through the user's Chrome browser (the
`claude-in-chrome` tools). The result is a saved design in the
`adrian@jetaasc.org` Canva account and a PNG that feeds
`jetaasc-event-publisher` and `jetaasc-newsletter-draft`.

A flyer should take about five minutes. Templates come from a vetted pool,
and every edit goes through panels and dialogs that the accessibility tree
exposes, so each step is addressable by element ref and verifiable by
reading the tree. Load `browser_batch` at the start and batch the
click/type/click sequences; a flyer is roughly a hundred browser actions.

## What goes on the flyer

Title, weekday and date, start and end time, venue with full street address,
cost with any caveat, and how to RSVP. Look up the address if only a venue
name was given. Voice is the usual JETAASC one: friendly, inclusive, short,
no em dashes. Event types are described in the repo's CLAUDE.md.

Write the copy to the template, not the other way round. Each replacement
should be no longer than the placeholder it replaces, in characters; that
single rule prevents nearly every wrap. If a detail will not fit its slot,
move it to a slot that has room (venue name in the column, street address
in the footer) rather than forcing a wrap.

## Session and account

The browser should already be signed in. If Canva shows a Log in button,
stop and ask the user to sign in; never enter credentials or use SSO
buttons. On first load expect a passkey prompt (skip), a Business trial
upsell (close), and a cookie banner (Manage cookies, Reject all).

The extension occasionally drops mid-session ("Browser extension is not
connected"). Call `tabs_context_mcp` and retry; the page state survives.

## Picking a template

Read [templates.md](templates.md). It is the pool of vetted templates, each
with the event types it suits, a description of its look, its text slots,
and when it was last used. Pick the entry that fits the event type, was
used least recently, and does not share a palette or motif with the two
most recent "last used" dates. Style comes before variety: an entry
flagged as a weak style fit is a last resort, not a rotation slot. Confirm the pick with the user unless they
have said to just go; the veto so far has been about feel, not fields.

Navigate straight to the entry's editor link. It creates a new design in
the current tab; no template page, no grid, no "Customize this template"
button. Update the entry's last-used date when the flyer is done.

The pool goes stale: Canva retires templates and the looks get familiar.
Two signals, both cheap to check while picking. If the pool file's "Last
scouted" date is more than about four months old, tell the user in the
final message that the pool is due for a `jetaasc-canva-template-scout`
run; mention it once and carry on, it never blocks a flyer. If an editor
link lands on an error page or an empty design instead of the template,
the template is gone: delete that entry and its thumbnail from the pool,
pick the next best entry, and say which one was removed. A section that
drops below three entries is worth calling out the same way.

Only if nothing in the pool suits the event, search
`https://www.canva.com/templates/?query=<terms>` and vet the find the way
`jetaasc-canva-template-scout` does, then add it to the pool so the next
run does not search. Search is the slowest part of the whole job.

## Editing method

### 1. Inventory the text

The canvas is in the accessibility tree as an application named "Canvas
content". `read_page` on it lists every element: text boxes as groups
whose children are the hard-broken lines, graphics as images. A group with
one child that renders on several lines is soft-wrapping, which matters
for step 4. This is the map of what to replace. The pool entry's slot list
is the same map written down in advance, so on a pool template the read
is a confirmation, not a discovery. `read_page` covers only the page in
view; a `javascript_tool` walk of `[aria-label="Canvas content"]` gets
the same inventory in one call. Have the script print each group's
aria-label and its leaf lines together, capped to a few lines per box,
so hard breaks come back in the same call and the output stays short.

The Layers tab (toolbar **Position** with any element selected) shows the
same elements as clickable buttons, which is the way to select a shape or
graphic, or to reach a text box's right-click menu. Layer labels show
rendered text, so a box styled in caps reads "3 PM TO 8 PM" there but
"3 PM to 8 PM" on the canvas; search with the canvas form. Canvas nodes
themselves are not clickable; their refs resolve to the page background.

### 2. Replace text with Find and replace

Click a blank spot beside the canvas so focus is on the page, then
`cmd+f` opens Canva's Find and replace. Type the placeholder string in
Find, the new string in Replace with, confirm the counter reads 1/1, click
Replace by ref. Styling is preserved and the edited element is left
selected. Typing a box's current text into Find is also the fastest way to
select that box for a font size change.

On a pool template the placeholders are known to be unique, so check the
counter on the first replacement and then batch the rest in one
`browser_batch`; the final screenshot catches anything that went astray.
A fresh template gets the counter check every time.

Matching is substring, so "NO" also hits "NOMIKAI" and "NOV". Search whole
placeholder strings; if the counter shows more than one match, use the
next/previous arrows to land on the right one or fall back to Magic Write.
The Replace field cannot hold a line break, so a multi-line box is replaced
one line at a time, which keeps the template's break in place.

### 3. Magic Write for the cases Find can't do

Right-click a text layer in the Layers tab, choose **Magic Write**, then
**Transform text**. A "Prompt anything" box appears. Prompts of the form
"Replace the text with exactly: FREE" or "Replace with exactly two lines.
Line 1: FRI. Line 2: OCT 30. No other text." came back verbatim. The result
is shown before it is applied; read it, then click Replace.

This costs a few round trips and several seconds of generation, and the
text is generated rather than typed, so check addresses and URLs in the
result. Use it for boxes whose placeholder text is not unique and for
writing several lines into one box.

### 4. Check fit, then fix it

After all replacements, take one screenshot. Wrapped or overlapping text is
obvious at a glance and a screenshot is cheaper than arithmetic for
spotting it. The selected element's floating toolbar can cover a
neighbor; if it does, the exported PNG (Read it from Downloads) is the
cleaner final check, since export ignores selection chrome. Fix a wrap by replacing the text again with shorter copy
(Find on the string you just inserted, counter 1/1), or by selecting the
box and typing a smaller number into the toolbar's font size combobox
(Enter commits). Font size scales height linearly, so two lines at 71 pt
become one line at about 60 pt.

Often the best fix is neither: widen the box. Templates leave text boxes
at the width of their placeholder, and a centred line on an 8.5 in page
can usually go to 7.5 in wide at X 0.5 in without touching anything else.
The Arrange tab (next to Layers) exposes Width, Height, X, and Y as
textboxes for the selected element; a wider box holds the full copy at
the template's own size, which looks better than a shrunk font. For an
overlap, read the neighbors' Y and Height to find the free gap, then type
a Y that fits. Commit Arrange fields with Tab; Enter drops the selection
before the value takes. A single line is roughly `size / 72 * 1.2` inches
tall, so `height` over that is the line count if you need it.

Two mechanics around the Arrange tab: the **Position** button is a
toggle, and the Find panel hides whether the panel is open, so after
selecting with Find click Position and check the tab is showing before
typing (twice if it was already open). Its field refs are regenerated
every time the panel opens, so each box needs a fresh `find` for its
Width and X; batch the edits per box, not across boxes.

Templates usually reserve one line per box. A title that becomes two or
three lines grows into whatever sits below it, so look at the neighbors
whenever a replacement adds a line. Removing a line moves things too:
grouped text is anchored at its centre, so a title that shrinks from
three lines to two shifts the whole group. Usually harmless, but it is
why the fit check comes after all replacements rather than during.

### Things that waste time

Panels, tiles, and buttons are always clicked by ref. Coordinate clicks on
the Find panel's close button and the Share panel's Download tile both
missed and closed the wrong panel.

Typing while no field or text box has focus sends every character to
Canva as a shortcut: `r` toggles rulers, `cmd+a` selects every element, and
a subsequent type call can rename or move things. Only type into a field
you have just clicked by ref.

Arrow-key nudging is unpredictable through the extension (a shift-arrow
moved about 100 px, not 10) and a click meant for a text box lands on the
background shape as often as not. Use the Y field instead.

Double-clicking canvas coordinates to enter edit mode works but needs a
fresh screenshot per box and misfires on grouped or overlapping elements.
It is the fallback, not the method.

## Pages, naming, export

Templates often carry extra pages; each page header has a trash icon. The
design title in the top bar is editable in place and the design auto-saves.
Title it `JETAASC <Event Name> <YYYY-MM-DD>`, with any colon or slash in
the event name dropped, since the title becomes the download filename.

Share (top right) opens a panel with a Download tile; PNG at the default
size is right for socials. The Download button can be disabled for a
moment while the panel loads; re-find it. Chrome saves to
`~/Downloads/<design name>.png`. Rename to the Public Flyers pattern
`JETAASC_<YYYY-MM-DD>_<Event_Name>.png` before it goes anywhere.

Always download. The PNG is the deliverable and the only thing the user
can check at a glance, so a flyer that stops at "saved in Canva" is not
finished. Adrian has given standing approval for the PNG export; do not
stop to ask, and send the file to the user (SendUserFile) rather than an
editor screenshot. Uploading to Drive or posting anywhere still waits for
the request that covers it.

## What JETAASC wants

**JETAASC's style is casual and Japan-oriented.** Hand-drawn or flat
illustration, warm palettes, Japanese motifs where they fit (noodle bowls,
seigaiha waves, sakura, torii, lanterns, kanji titles). What it is not:
corporate or networking. Icon rows, "what to expect" grids, globe logos,
calendar and pin glyphs, hazard stripes and boxed agendas all read as a
tech meetup, and a flyer built on them gets vetoed even when every detail
fits. Boba Banter can lean a little more polished than a nomikai, but it
is still a tea shop, not a conference. The pool is curated to this bar;
if the only entry that fits the slots looks like a meetup, pick the one
that looks like JETAASC and adjust the copy.

**Variety across events.** Flyers appear side by side in the newsletter,
Discord, and Facebook, so consecutive flyers should differ in palette and
motif. The pool's last-used dates are how you know what ran recently. When
fit and variety conflict, fit wins; a clean flyer in a familiar style beats
a wrapped one in a fresh style.

**Handoff.** Upload to Public Flyers with `anyone:reader` per
[../../references/public-flyers.md](../../references/public-flyers.md),
then pass the file to `jetaasc-event-publisher` or
`jetaasc-newsletter-draft`. Facebook's `file_upload` only takes paths inside
the session scratchpad, so copy the PNG there for that step.
