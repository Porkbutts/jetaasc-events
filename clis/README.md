# clis

Small, self-contained CLIs for JETAASC event publishing. Python 3 stdlib only —
no dependencies, no virtualenv.

| CLI | Source | Docs | What it does |
|-----|--------|------|--------------|
| `partiful` | [partiful.py](partiful.py) | [partiful.md](partiful.md) | Create, update, get, delete Partiful RSVP pages |
| `dc` | [dc.py](dc.py) | [dc.md](dc.md) | Discord: post/read messages, publish threads, manage scheduled events |

## Install

Both are run by name, from any directory. Symlink them onto your PATH:

```sh
ln -s "$(pwd)/partiful.py" ~/.local/bin/partiful
ln -s "$(pwd)/dc.py"       ~/.local/bin/dc
partiful --help
dc --help
```

Each script resolves its own symlink when locating config, so credentials are
read from this repo no matter which directory you invoke from.

## Credentials

| CLI | Source | Notes |
|-----|--------|-------|
| `partiful` | `clis/.partiful-auth.json` | Gitignored. Created by `partiful login`; refresh token auto-renews per command. Override the path with `$PARTIFUL_AUTH`. |
| `dc` | `$DISCORD_BOT_TOKEN`, else the first `.env` found in the current dir, `clis/`, or the repo root | Gitignored. Posts as the **JETAASC Assistant** bot. |

Neither credential is ever committed — see the repo `.gitignore`.

## Used by

The `jetaasc-event-publisher` skill drives both: `partiful` for the RSVP page,
`dc` for the Discord scheduled event. See
`.claude/skills/jetaasc-event-publisher/references/`.
