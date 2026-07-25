---
name: jetaasc-correspondence
description: Draft email replies on behalf of JETAASC to anyone who writes in — volunteer form submissions, prospective speakers, venues, sponsors, returning JETs, prospective applicants, general inquiries. Use when the user wants to answer, reply to, respond to, follow up with, or write to a person or group. Triggers include "draft a reply to", "respond to X", "email X back", "draft an email to X", "follow up with X", "answer this inquiry". Always produces an unsent Gmail draft for review.
---

# JETAASC Correspondence

Drafts email as Adrian for JETAASC. The output is always an unsent Gmail draft
plus the full text in chat, so nothing reaches a real person unreviewed.

## Non-negotiables

1. **Never send.** Create drafts only. Do not call `messages.send` or
   `drafts.send` unless the user explicitly says to send, in that message.
2. **Never invent facts.** No event that isn't scheduled, no date you didn't
   read, no org policy you didn't verify. See "Research first".
3. **Never promise a role, slot, or commitment** on the board's behalf. Offer a
   conversation instead: "let's work out where it fits" not "you're in".
4. **No em dashes** anywhere in drafted copy.
5. **Surface your judgment calls** after the draft. Every hedge, omission, and
   assumption gets one line so the user can overrule it.

## Research first

This is the part that makes a reply worth sending. Do it before writing a word.

**What did they actually say?** Read their own words and reflect specifics back.
A reply that could have been sent to anyone reads as a form letter.

- Inbound email: `gws gmail users messages list --params '{"userId":"me","q":"from:their@email"}'`
- Volunteer interest form responses live in the sheet in `references/sources.md`

**Who are they?** Check for prior contact before assuming a cold intro.
Search their address across the whole mailbox, not just the inbox.

**What is actually happening at JETAASC right now?** Pull the current newsletter
and read the upcoming events: real dates, venues, cities, costs, RSVP links,
event contacts. Method is in the root `CLAUDE.md` under Mailchimp.

This is where a generic reply becomes a specific one. A volunteer in Tustin is
worth far more than a "let's grab coffee sometime" when there is already a
JETAASC event in Tustin on the 22nd that they can be pointed at. Look for the
overlap between what they want and what is already on the calendar.

**Ask the user for anything only they know.** Prior relationship, whether the
person already RSVP'd, whether an event is scheduled or merely intended. Do not
guess at these, and do not assert them in the draft.

## Tone

Friendly, inclusive, community-oriented. Concise and skimmable. Volunteer-run
and budget-conscious, so warm but not corporate.

- Reference their specifics. Their placement, their skills, their question.
- Answer the question they actually asked, first.
- Hedge uncertain memory: "I'm fairly sure we've crossed paths" survives being
  wrong. "Great to see you again" does not.
- Declining: state it plainly in one line, no invented justification. "I don't
  have a role to match you with at the moment" needs no policy behind it.
- Sign off `Adrian` on its own line. The signature block carries the title.

## Writing the draft

Use `scripts/draft.py`, which handles the plumbing that is easy to get wrong:
multipart/alternative, the live signature, and reply threading.

```bash
python3 .claude/skills/jetaasc-correspondence/scripts/draft.py spec.json
```

`spec.json`:

```json
{
  "to": "person@example.com",
  "subject": "Welcome back, and what's coming up",
  "body": "Hi Darianne,\n\nParagraphs separated by blank lines.\n\nAdrian",
  "reply_to_message_id": "19f97c845219f89f"
}
```

`reply_to_message_id` is optional. Include it to reply inside an existing
thread; the script reads that message's `Message-ID` and `threadId` and sets
`In-Reply-To`, `References`, and a `Re:` subject so Gmail threads it. Omit it
for a new conversation.

Then paste the full body into chat for review, and list your judgment calls.

## Signature

The Gmail API does not apply signatures; the web compose window does. So a draft
created here is unsigned unless the script appends it, which it does, reading the
live HTML from `sendAs` settings so edits in Gmail are picked up automatically.

The token can read `sendAs` but not write it. Setting a signature via API needs
the `gmail.settings.basic` scope, which is not granted. To change a signature,
the user edits it in Gmail settings.

## Auth

Per root `CLAUDE.md`: check `gws auth status` first. The active account must be
`adrian@jetaasc.org`.

## Reference

- `references/sources.md` — sheet IDs, URLs, and where recurring facts live
