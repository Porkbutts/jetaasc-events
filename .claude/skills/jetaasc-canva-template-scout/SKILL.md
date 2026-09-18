---
name: jetaasc-canva-template-scout
description: Find and vet Canva templates for JETAASC event flyers and record them in the template pool that jetaasc-canva-flyer draws from. Use when the pool is thin for an event type, when the user wants more or different flyer looks, or when a flyer run had to fall back to searching. Triggers include "find flyer templates", "scout templates", "add templates to the pool", "we need more nomikai templates", "refresh the template pool".
---

# JETAASC Canva Template Scout

Do the template legwork once so that `jetaasc-canva-flyer` never searches.
The output is new entries in
[../jetaasc-canva-flyer/templates.md](../jetaasc-canva-flyer/templates.md),
each with a direct editor link, a look description, and a slot list. Drive
Canva through Chrome (`claude-in-chrome`); the account and session notes in
the flyer skill apply here too.

## What the events are

A template is judged on whether its slots hold what the event needs, so
know the events before searching (CLAUDE.md has the fuller descriptions):

- **Boba Banter** is a talk by one JET alum about their post-JET career,
  held at a boba or tea shop, followed by open conversation. The flyer
  needs a speaker line and a short blurb, a date, time, venue, cost (free,
  buy your own drink) and RSVP. There is never a speaker photo.
- **Nihongo Dake Dinner** is a group meal where people practise Japanese.
  No speaker. Needs date, time, restaurant and address, a cost note, and a
  sentence that all levels are welcome; sometimes a nijikai note.
- **Natsukashii Nomikai** is drinks at a brewery with no agenda beyond
  reminiscing about Japan. The flyer is mostly date, place and mood, plus
  a cost caveat.
- **Mixers and other socials** vary; date, place, cost and RSVP are the
  constants, and a two-line blurb is usually wanted.

## What a pool entry needs

An entry exists so the flyer run can decide without opening Canva. Record:

- **Template page URL**, and the **editor link** taken from the
  "Customize this template" button's `href` on that page. Navigating to the
  editor link creates a fresh design directly, which is faster and more
  reliable than clicking the button. The link has the shape
  `/design/editor/shell?create&type=<id>&template=<template id>&category=<id>`;
  drop the `analyticsCorrelationId` parameter.
- **Look**: palette, motif, illustrated versus typographic, page size. Two
  or three phrases are enough; this is what the variety rule compares.
- **Slots**: every text box in reading order with its placeholder text and
  a rough character width, and whether a box is one line or several. Copy
  gets written to these widths before Canva is opened, so they matter more
  than anything else in the entry.
- **Watch**: anything that bit during vetting, such as a graphic that
  overlaps a text box, grouped boxes near the page edge, or a title split
  into two boxes.
- **Last used**: blank for a new entry.

## Where to look

`https://www.canva.com/templates/?query=<terms>` searches directly. Query
by mood and object rather than by the event. Queries that have produced
usable candidates: "matcha flyer", "bubble tea flyer" and "coffee chat
flyer" for Boba Banter; "ramen flyer" and "japanese restaurant flyer" for
NDD; "beer night flyer" for nomikai; "language exchange meetup flyer" and
"japanese poster" for mixers. Queries that have not: "career talk" and
"guest speaker" (headshot layouts), "brewery flyer" (logos), "japanese
dinner" (generic party invitations). Check the results heading, because
Canva autocorrects unknown words ("izakaya" became "izaak"). Results wander
off-topic after the first couple of rows; two or three scrolls per query is
enough, and `scroll` returns its own screenshot, so do not add one.

Each result card's `aria-label` reads like "Preview free <name> template,
2 pages", which gives free-versus-Pro and the page count without a
screenshot. Reading those labels with `javascript_tool` covers a whole
results page in one call, provided the script filters to free flyer and
poster cards and trims each line to the name and the eleven-character
id; the tool truncates results at about a thousand characters. A
contact sheet of several previews (tile them with PIL) judges look
faster than opening each one. Wait a
few seconds after navigating to a results page before listing, or the
list comes back empty. Queries that also fail: "sake flyer" (autocorrects
to "sale") and "japanese pub flyer" (pub quizzes).

Per event type, the vibe to look for:

- **Boba Banter**: professional but warm. Cafe, coffee, tea, matcha, talk.
- **Nihongo Dake Dinner**: warm and Japanese-flavoured. Ramen, noodle,
  restaurant, izakaya if it survives autocorrect.
- **Natsukashii Nomikai**: casual social. Beer night, happy hour, pub.
- **Mixers and general socials**: friendly and open. Meetup, community,
  language exchange, festival, Japanese pattern.

## Vetting a candidate

JETAASC's style is casual and Japan-oriented: hand-drawn or flat
illustration, warm palettes, Japanese motifs (noodle bowls, seigaiha
waves, sakura, torii, lanterns, kanji) where they suit the event. The
test for a candidate is whether it could be for a community of friends
who lived in Japan. Anything that reads as a tech meetup, a corporate
networking night, or a gig poster fails that test no matter how good its
slots are: icon rows, "what to expect" grids, globe or handshake logos,
calendar and pin glyphs beside the logistics, hazard stripes, boxed
agendas. A language-exchange flyer with a globe logo and four round icons
was built into a real flyer and vetoed on sight; that is the bar. A
single removable glyph on an otherwise strongly Japanese or hand-drawn
template does not fail it; note "delete the glyph from Layers" in Watch.
Commercial promotions (discount badges, "order now", package prices) do
fail it, with one allowance: restaurant-promo templates are the only
place Japanese food illustration turns up, so an NDD entry may carry a
"best seller" line as long as the flyer skill can replace it.

Reject on any of these before recording:

- A look that fails the style test above. Check this first; it is the
  commonest reason a slot-perfect template is wrong.
- A crown badge on the result card. Pro templates are out.
- A headshot or photo slot the layout depends on. JETAASC rarely has one.
- Text boxes narrower than about 12 characters at the template's size for
  the slots that must hold a date, a venue, or an address. Titles can be
  short; logistics cannot.
- More than one page, unless the extra pages are obviously disposable.

To measure the slots, open the editor link and inventory the "Canvas
content" application. Each text box is a group whose children are the
hard-broken lines; the placeholder text and its length give the width.
`read_page` on the application works but only covers the page in view, so
scroll before reading a second page. Faster is one `javascript_tool` call
that finds `[aria-label="Canvas content"]` and walks its children for
aria-labels and leaf text; that gives the whole inventory in a single
round trip. A text box is an aria-labelled node with no aria-labelled
descendants; the "Canvas content" node and the page group carry labels
too, so filter to the leaves. Canva paints the labels before the text and
first shows "Screen reader content is loading", so poll until the
canvas's `textContent` is past about 40 characters and no longer
contains that phrase; use `textContent`, never `innerText`, which forces
layout and can hang the call. Strip `?`, `&` and `=` from every result,
not only hrefs; a placeholder containing them trips the same filter.
Letter-spaced boxes can come back as one- or two-letter fragments;
record them as one box. Select a box (type its text into Find and replace, `cmd+f`)
and read the Arrange tab's Width to get inches only if the character
estimate looks doubtful; it rarely does.

Take the page size from the template page's subtitle ("Flyer (Portrait
US) • 8.5 × 11 in"). The editor's title-bar suffix is a document type, not
a size, and says "Real Estate Flyer" for every 8.5 x 11 template.

`javascript_tool` refuses to return any string containing a query string,
which includes every editor link. Read hrefs with `?`, `&` and `=` swapped
for placeholder tokens and swap them back; the tokens pass the filter.
The editor link can also be assembled from the pattern above once the
template id is known, and confirmed against the real href in the same
batch.

A vetting design is disposable. Do not rename it or export it; Canva keeps
it in the account, which is harmless.

## Recording

Append to the right event-type section of `templates.md`, matching the
existing entries' shape. Five entries per event type is the target, ten
for Boba Banter and for mixers and general socials, the two that run
most often and cover the widest range of events.
If a candidate suits two event types, file it under the closer one and
say so in Look.

Save a thumbnail as `thumbs/<template id>.jpg` beside `templates.md`, so
the pool can be rendered as a gallery (`scripts/pool-gallery.py` at the
repo root, which takes an output path) and reviewed by eye. Write each
entry and its thumbnail as soon as it is vetted rather than at the end,
so a cut-off run leaves the pool consistent. On the template page the flat preview is the largest
`img` whose source is on `template.canva.com`; it arrives a few seconds
after the mockup carousel, so poll for it in `javascript_tool` (top-level
`await` works) rather than waiting a fixed time. Its URL is signed and
short-lived, so read it (with the query-string tokens swapped as above),
`curl` it straight away, and shrink it with `sips -Z 520`. A page
screenshot is not a substitute; it shows the mockup, not the template.

Aim for spread within a section: not all cream, not all line-art, at least
one typographic option. That spread is what lets the flyer skill honour
the variety rule without searching.
