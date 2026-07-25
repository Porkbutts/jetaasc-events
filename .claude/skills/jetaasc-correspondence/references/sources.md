# Sources

Where recurring facts live. Verify before quoting any of it in a draft; these
are pointers, not a cache.

## Volunteer Interest Form (responses)

Spreadsheet: `1QIFm6H9KDnh3TyrbHV_A0e4VOVCWCth4_wgxIali_Mk`
Tab: `Form Responses 1`

```bash
gws sheets +read --spreadsheet 1QIFm6H9KDnh3TyrbHV_A0e4VOVCWCth4_wgxIali_Mk \
  --range "'Form Responses 1'!A1:P200"
```

Columns: Timestamp, Email, First Name, Last Name, Current City, JET Placement,
Year(s) on JET, Which role(s) interest you, a long free-text field about
interests and skills, Additional Comments.

Notes on reading it:

- Submissions are sparse, a few per year, so filtering by year leaves very few
  rows. Read the whole sheet and filter in code.
- People re-submit when they get no reply, so the same name can appear more than
  once with different dates. Check for duplicates before treating one as new.
- "Current City" can be in Japan for someone still on JET. It is where they were
  when they applied, not where they are now.
- Roles offered on the form: Area Representative, Event Coordinator, Content
  Contributor.
- Public form: https://jetaasc.org/volunteer-interest-form

## Newsletter

Signup, safe to hand out: https://jetaasc.org/newsletter-signup

Campaign archive is the best source for what is actually scheduled: dates,
venues, costs, RSVP links, and named event contacts. Query method is in the root
`CLAUDE.md` under Mailchimp. The current month's issue is the one to read before
pointing anyone at an event.

## Recurring event formats

Described in the root `CLAUDE.md`: Boba Banter (career talks), Nihongo Dake
Dinner (Japanese practice), Natsukashii Nomikai (nostalgic social). Useful when
someone wants to help but has no specific idea, since it turns an open question
into picking from a menu.

## Other channels

- Discord, for internal discussion such as `#officer-meetings`: `dc` CLI. See
  the `jetaasc-event-publisher` skill.
- Google Calendar: https://calendar.google.com/calendar/u/0/embed?src=jetaasc.org_hjd9mjsdhqrniqbfup80ctf9pc@group.calendar.google.com
- Facebook group: https://www.facebook.com/groups/jetaasc/events
