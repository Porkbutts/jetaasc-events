---
name: jetaasc-newsletter-discord-review
description: |
  Sweep Discord for anything the upcoming JETAASC newsletter is missing: officer chatter that
  implies an announcement or event change, and new job postings worth featuring.
  Use before building or sending a monthly issue, or when the user asks what the newsletter
  might be missing. Triggers: "review discord for the newsletter", "check discord before I send",
  "any job postings for the newsletter", "what did the officers say about X",
  "is the newsletter missing anything", "harden the newsletter".
---

# Newsletter Discord Review

Read-only sweep of Discord for content the monthly issue should carry but does not.

Run it **before** the campaign goes out. It exists because the newsletter is assembled
from a Google Doc that board members forget to update, while the real decisions happen
in chat. Twice now the doc has been complete and the issue still wrong: a venue changed
after the flyer was made, and three job postings existed that the doc said were none.

**This skill never posts, reacts, edits, or sends.** It reads Discord and reports. Any
change it turns up goes into the monthly doc via `jetaasc-newsletter-draft`, or into the
campaign via `jetaasc-newsletter`.

## Channels

| Channel | ID | Type | Holds |
|---|---|---|---|
| `🤝officer-meetings` | `1178481630667624528` | text | Meeting coordination, event scheduling, decisions |
| `👮officers-n-board` | `1221681227178709032` | text | Board-level discussion, announcements in the making |
| `👔job-opportunities` | `1081705416054026301` | **forum** | Job postings, one per forum thread |

Default window is the last 4 weeks. Widen it when an issue slipped, or when the user
names a longer period.

## Reading the text channels

`dc` addresses channels by name fragment, and `--after` takes a message id, not a date.
Convert the window start to a snowflake:

```bash
python3 -c "
import datetime
dt = datetime.datetime(2026, 8, 6, tzinfo=datetime.timezone.utc)   # window start
print((int(dt.timestamp()*1000) - 1420070400000) << 22)"
```

```bash
dc messages list officer-meetings --after <SNOWFLAKE> --all > om.json
dc messages list officers-n-board --after <SNOWFLAKE> --all > onb.json
```

`--all` really does page; a result of exactly 50 is the page size, not proof of the total.
Confirm by widening the window and checking the count grows.

Render with author, local time, and reply target. Resolve `<@id>` mentions where the id
appears as a message author somewhere in the pull, so the transcript reads as a conversation.

## Reading the job forum

**`👔job-opportunities` is a forum channel (type 15). `dc messages list` on it returns an
empty list, not an error.** Each posting is a *thread* whose id is also its first message
id. `dc` has no thread-listing command, so call the API directly.

**Do not `source` the `.env`.** `DISCORD_USER_AGENT` contains parentheses and shells fail
to parse it. Read it in Python:

```python
env = {}
for line in open('.env'):
    line = line.strip()
    if not line or line.startswith('#') or '=' not in line: continue
    k, v = line.split('=', 1)
    env[k.strip()] = v.strip().strip('"').strip("'")
```

Then list both live and archived posts, since a posting older than a few days is archived:

```
GET /guilds/{guild}/threads/active           # filter parent_id == forum id
GET /channels/{forum}/threads/archived/public?limit=25
```

Headers: `Authorization: Bot <token>`, `User-Agent: <DISCORD_USER_AGENT>`. Discord's edge
403s a default urllib user-agent.

Fetch each thread's messages with `GET /channels/{thread_id}/messages?limit=50`. The first
message is the posting; later ones are replies and often irrelevant.

## Job postings usually hide their real content in a PDF

A posting's Discord text is a summary. The attached PDF carries the pay range, the full
date list, and, critically, **how to apply**, which is frequently absent from the message
itself. A listing with no apply route is not usable in the newsletter.

1. Download the attachment from `attachments[].url` (send the user-agent header; the bot
   token is not needed for the CDN).
2. Extract the text and read it:
   ```python
   from pypdf import PdfReader
   txt = "\n".join(p.extract_text() for p in PdfReader(path).pages)
   ```
   Extracted text is full of stray whitespace. Collapse it before reading, or the apply
   line will be hard to spot at the end of page 2.
3. Re-host the PDF (below) and link it, rather than pointing readers at Discord. **Most of
   the ~1,500 person list is not in the Discord server**, so a Discord link is a dead end
   for them.

### Re-hosting a PDF on Mailchimp

The `mailchimp_upload_image` MCP tool takes images only. PDFs go through the File Manager
REST endpoint, which accepts any file type and returns a public URL:

```
POST /3.0/file-manager/files
{"name": "gpi-us-facilitator-2026-2027.pdf", "file_data": "<base64>"}
```

Auth is HTTP basic (`any:$KEY`); the datacenter is the suffix after the dash in the key.
See CLAUDE.md for pulling the key out of `.mcp.json`. Use the returned `full_size_url`,
and verify it before shipping it:

```bash
curl -s -o /dev/null -w "%{http_code} %{content_type}\n" "<full_size_url>"   # expect 200 application/pdf
```

Name files descriptively (`<org>-<role>-<term>.pdf`). Delete any test upload you make:
`DELETE /3.0/file-manager/files/{id}`.

Google Drive Public Flyers also works and is the right home for *flyer art*. For job
description PDFs prefer Mailchimp: it keeps the issue's assets together and skips the
`anyone:reader` step that fails silently. See
[../../references/public-flyers.md](../../references/public-flyers.md).

## Writing up a job listing

These are other people's postings. **Stay close to the poster's wording** rather than
rewriting into house voice; the details are load-bearing and paraphrase drops them.

Every listing needs a role, an organization, enough scope for a reader to self-select, and
a working way to apply. Carry over what the poster wrote; pull pay and apply route from the
PDF when the message omits them, and link the PDF for the rest.

Reasonable to drop: internal program codes, "see attached flier", "first of 2" framing,
and other Discord-specific scaffolding. Never drop the apply route.

## What to report

Report to the user, do not act unilaterally:

- **Contradicts the newsletter.** A venue, date, or price that changed after the doc was
  written. Highest priority; this is the class of error that reaches 1,500 inboxes.
- **Missing content.** Job postings, announcements, or events discussed but never added.
- **Decisions and permissions.** Photo approvals, someone taking an assignment, a date
  pinned down. Often answers a question the newsletter build is blocked on.
- **Next month.** Anything too late for this issue but worth remembering.

Quote the relevant message and name who said it, so the user can judge without rereading
the channel. Flag anything ambiguous rather than resolving it yourself: chat is full of
half-decisions, and a confident misreading becomes a wrong line in an email.

## Privacy

Officer channels are private. Nothing from them goes into the newsletter verbatim without
the user's say-so, and personal chatter stays out of the report. Photos of members,
especially minors, need explicit permission from the person who posted them; that
permission is often given in-channel and worth surfacing when it exists.
