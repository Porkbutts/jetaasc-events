# partiful

An unofficial CLI for Partiful, which has no public API. Each command maps to
the call the web app makes, and prints JSON. General-purpose: nothing in it is
specific to JETAASC.

Run `partiful --help` and `partiful <command> --help` for the command reference.
The subcommand help carries the full flag list plus the parts worth spelling out
(UTC handling, structured locations, the RSVP question format, non-interactive
login), so this file sticks to how the thing works underneath.

Python stdlib only, run by name from anywhere via a symlink on `PATH`.

## Auth

Firebase phone auth: SMS code, exchanged for a custom token, exchanged for a JWT
plus a refresh token. Only the refresh token and uid are persisted; every command
trades the refresh token for a fresh JWT and saves the rotated one, so a login
lasts until the file is lost or the token is revoked.

```sh
partiful send-code 8185551234
partiful login 8185551234 --code 123456
```

`login` without `--code` prompts on stdin and needs a terminal; with stdin not a
TTY it exits with the two-step recipe rather than blocking on a prompt that can
never be answered. Phone numbers take either `8185551234` (assumes US `+1`) or
`+18185551234`.

Credentials live in `.partiful-auth.json` beside the script (gitignored), or
wherever `PARTIFUL_AUTH` points. The path is resolved through symlinks, so the
`~/.local/bin/partiful` symlink finds the file next to the real script.

Token refresh requires a `Referer: https://partiful.com/` header; without it
Google returns 403. Already handled, but it is why the header is there.

## Endpoints

| Command | Call |
|---------|------|
| `create` | `POST api.partiful.com/createEvent` |
| `--image` | `POST api.partiful.com/uploadPhoto?uploadType=event_poster` (multipart), then a Firestore PATCH linking the upload |
| `update`, `get`, `delete` | Firestore REST directly (`firestore.googleapis.com`, project `getpartiful`) |

`create` posts the event, then PATCHes location, questions, image, and the public
flag onto the new document — those fields either need Firestore's typed encoding
or an upload round-trip first, so they don't ride along in the create body.

## Notable behavior

**Times are absolute.** `--date`/`--time` are UTC and stored as an instant.
`--timezone` only tells Partiful how to label that instant on the event page; it
does not shift it.

**Locations are built locally.** Given `"Venue, Street, City, ST ZIP"` the CLI
constructs the `locationInfo` map Partiful needs for a map pin — address lines,
approximate location, Apple and Google Maps URLs — from the address text alone.
No geocoding, so no Google API key. Fewer than three comma-separated parts sets
only the display name, and the page shows "no location set".

**Questionnaires are append-only.** `questionnaireEnabled` gates the feature and
`questionnaireVersions` holds the history; Partiful treats the last entry as live.
Each guest's response records the *index* of the version it answered, so an update
appends a version rather than rewriting the array — overwriting in place would
silently repoint old answers at different questions. `--no-questionnaire` flips
the flag and touches nothing else.

Question types (`short_answer`, `select`, `email`, `instagram`, `twitter`,
`tiktok`, `snapchat`, `linkedin`) are Partiful's own enum, read out of the web
app's JS bundle. A type outside that set will store fine and render wrong.

**`get` is a thin read.** It prints the document's top-level fields, unwrapping
one layer of Firestore's typed encoding. Nested maps and arrays keep their
`{"stringValue": ...}` form.

**`delete` is permanent** and takes no confirmation.
