---
name: jetaasc-canva-flyer
description: Create a JETAASC (JET Alumni Association of Southern California) event flyer in Canva by driving the Chrome browser with Claude in Chrome. Use when the user wants a flyer, graphic, or image for an event to share on socials, the newsletter, Discord, or Facebook. Triggers include "make a flyer", "canva flyer", "create a flyer for", "design a graphic for the event", or any request for event artwork. Produces a saved Canva design and, with permission, a PNG export.
---

# JETAASC Canva Flyer

Build an event flyer in Canva through the user's Chrome browser (the
`claude-in-chrome` tools). The result is a saved design in the
`adrian@jetaasc.org` Canva account and a PNG that feeds
`jetaasc-event-publisher` and `jetaasc-newsletter-draft`.

## What goes on the flyer

Title, weekday and date, start and end time, venue with full street address,
cost with any caveat, and how to RSVP. Look up the address if only a venue
name was given. Voice is the usual JETAASC one: friendly, inclusive, short,
no em dashes. Event types are described in the repo's CLAUDE.md.

## How Canva behaves

**Account.** The browser should already be signed in. If Canva shows a Log in
button, stop and ask the user to sign in; never enter credentials or use SSO
buttons. On first load expect a passkey prompt (skip), a Business trial
upsell (close), and a cookie banner (Manage cookies, Reject all).

**Templates.** `https://www.canva.com/templates/?query=<terms>` searches
directly. Results are ranked loosely and wander off-topic after the first
couple of rows. A crown badge means Pro; stick to free templates.
"Customize this template" opens the design in a new tab.

**Editing text.** Double-click a text box to enter edit mode, `cmd+a` to
select its contents, type to replace, Escape to leave. Grouped text still
edits per box. Multi-line text must be one `type` call with `\n` in the
string: separate Return key presses between type calls arrive out of order.
Canva auto-superscripts ordinals like "2ND".

**Pages and naming.** Templates often carry extra pages; each page header
has a trash icon. The design title in the top bar is editable in place and
the design auto-saves.

**Export.** Share (top right) opens a panel with a Download tile. PNG at the
default size is right for socials. Chrome saves to
`~/Downloads/<design name>.png`. Downloading needs the user's OK, and
"take the flyer and post it" counts as one.

## What JETAASC wants

**Template matches the vibe, not the word "event."** A corporate networking
template is wrong for a nomikai even if it has the right text slots. Casual
socials want something warm and Japanese-flavoured; Boba Banter can look
more professional. Confirm the pick with the user before editing; the veto
so far has been about feel, not fields.

**Variety across events.** Flyers appear side by side in the newsletter,
Discord, and Facebook. Read [templates-used.md](templates-used.md) first,
avoid anything used in the last six months, and steer away from the look of
the last two entries (palette, motif, illustrated versus typographic). Log
the new template when done.

**Naming.** Design title `JETAASC <Event Name> <YYYY-MM-DD>`. Exported file
renamed to the Public Flyers pattern `JETAASC_<YYYY-MM-DD>_<Event_Name>.png`
before it goes anywhere.

**Handoff.** Upload to Public Flyers with `anyone:reader` per
[../../references/public-flyers.md](../../references/public-flyers.md),
then pass the file to `jetaasc-event-publisher` or
`jetaasc-newsletter-draft`. Facebook's `file_upload` only takes paths inside
the session scratchpad, so copy the PNG there for that step.
