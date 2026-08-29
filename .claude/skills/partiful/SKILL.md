---
name: partiful
description: Create, update, get, and delete events on Partiful using the `partiful` CLI. Use when user wants to publish, create, update, or delete a Partiful event. Triggers include "partiful", "create partiful event", "publish to partiful", or any Partiful-related task.
---

# Partiful

`partiful` is a general-purpose CLI and documents itself. **Get the command
reference from the CLI, not from this file:**

```bash
partiful --help
partiful create --help      # also: UTC handling, structured locations, RSVP questions
partiful update --help      # also: how question sets are versioned
partiful login --help       # also: the non-interactive login flow
```

Every flag, every theme and effect name, and every RSVP question attribute is in
there, and it cannot drift out of date the way a copy here would. Don't guess at
arguments — read the help for the subcommand you're about to run.

This skill covers only the things `--help` can't know: this environment, and how
JETAASC uses the tool.

## Setup

`partiful` is on PATH via a symlink at `~/.local/bin/partiful` pointing at
`clis/partiful.py` in this repo. Recreate it if it goes missing:

```bash
ln -s "$(pwd)/clis/partiful.py" ~/.local/bin/partiful
```

Auth lives in `clis/.partiful-auth.json` (gitignored). The refresh token renews
on every command, so once logged in it stays working. Python stdlib only, no
install step.

## Gotchas in this environment

**`!` gets mangled.** The Bash tool sandbox rewrites `!` to `\!` inside
arguments, which lands literally in the event title, description, or question
text. Wrap any text containing `!` in a heredoc:

```bash
partiful create \
  --title "$(cat <<'EOF'
Natsukashii Nomikai!
EOF
)" \
  --description "$(cat <<'EOF'
Come reminisce! First round's on us.
EOF
)" \
  # ... other args
```

**Logging in needs a human.** `partiful login <phone>` without `--code` prompts
on stdin; from the Bash tool it exits with an error rather than prompting. Auth
should already be valid, but if it isn't:

1. Ask the user for their phone number.
2. `partiful send-code <PHONE>`
3. Ask the user for the SMS code with `AskUserQuestion`.
4. `partiful login <PHONE> --code <CODE>`

Never invent a phone number or code, and don't send a code to a number the user
didn't give you.

## JETAASC conventions

**This skill is usually reached from `jetaasc-event-publisher`,** which has
already collected the title, date, location, description, and flyer. Use those
details — don't re-interview the user.

**Times.** The CLI takes UTC. Our events are Pacific, so:

- PST (Nov–Mar): add 8 hours — 6:00pm PST is `--date <next day> --time 02:00`
- PDT (Mar–Nov): add 7 hours — 6:00pm PDT is `--date <next day> --time 01:00`

Leave `--timezone America/Los_Angeles` (the default); it only sets how the page
labels the time, it does not convert what you passed. Sanity-check the result on
the event page — an evening event that renders as a morning one is an offset
applied backwards.

**Visibility: link-only.** Omit `--public` unless the user asks to list the event
on Partiful's Explore feed. The RSVP link still works for anyone who has it.

**Questions: none by default.** RSVP friction costs turnout, and the events are
usually come-as-you-are. Add questions only when the event genuinely needs the
answer, and offer rather than assume. Reasonable cases:

- Nihongo Dake Dinner or a nomikai with a set menu or a reserved table —
  `--question "Any dietary restrictions?"`
- Anything with a headcount-driven cost — a required dropdown beats a comment
  thread.
- Boba Banter and other drop-in events — usually nothing.

Note that Partiful questions cover most of what we used to need a Google Form
for; check `partiful create --help` for the available question types before
reaching for a separate form.

**Theme and effect: match the event.** There's no house style. Pick something
that fits the vibe (a nomikai reads differently from a professional development
talk) and mention what you chose so the user can veto it.

**Location: give the full street address** — `"Venue, Street, City, ST ZIP"` — so
the event page gets a real map pin. A bare venue name renders as "No Location
Set", which is a bad look for a first-time attendee trying to find us.

**Voice.** Same as everything else JETAASC-facing: friendly, inclusive, concise,
no em dashes. Event types (Boba Banter, Nihongo Dake Dinner, Natsukashii Nomikai)
are described in the repo's CLAUDE.md.

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `No auth config found` | `clis/.partiful-auth.json` is missing | Run the login flow above |
| `HTTP 401` | Refresh token expired or revoked | Same — re-run the login flow |
| `login ... stdin is not a terminal` | Called `login` without `--code` | Use `send-code`, then `login --code` |
