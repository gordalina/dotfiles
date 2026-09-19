# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Personal macOS dotfiles for `gordalina`. The repo lives at `~/src/dotfiles` and its
contents are symlinked into `$HOME` by [mise](https://mise.jdx.dev). There is no build
or test suite — "running" this repo means applying config to the live machine.

## Key commands

- `mise bootstrap` — read `.config/mise/config.toml` `[dotfiles]` table and symlink each
  repo path into `$HOME` (e.g. `.config`, `.ssh`, `bin`, `.zshenv`). This is how changes
  in the repo take effect. `dotfiles.default_mode = "symlink"`, so edits to repo files are
  live immediately for already-linked paths.
- `bin/dot` — apply all macOS `defaults`/`scutil` system preferences. **Destructive and
  sudo-heavy**: disables Gatekeeper, wipes the Dock, kills Finder/Dock.
  Only run on a machine intended to be configured as this workstation.
- `brew bundle` — install everything in the top-level `Brewfile` (symlinked to `~/.Brewfile`).
- `install.sh` — full first-run bootstrap for a fresh Mac (Xcode CLT → Homebrew → clone repo
  → `mise bootstrap` → `bin/dot` → `brew bundle`). Meant to be curl-piped, not run locally.

There are no lint/test commands. To verify a shell change, `source ~/.config/zsh/.zshrc`
(aliased `reload!`) or open a new shell.

## Architecture

**mise is the dotfiles manager**, not GNU stow/chezmoi. The source of truth is the
`[dotfiles]` table in `.config/mise/config.toml`: each `"~/target" = {}` entry is symlinked
from the matching repo path. `[tools]` pins language/CLI versions (elixir, erlang,
claude-code, etc.). `.config/mise/config.local.toml` is machine-local (repos to clone) and
should not hold anything meant to be shared.

**Shell config is XDG-based and modular.** `.zshenv` sets `ZDOTDIR=$XDG_CONFIG_HOME/zsh`,
so zsh reads from `.config/zsh/`, not `~`. `.config/zsh/.zshrc` sets the XDG vars then
sources every `.config/zsh/zsh.d/*.zsh` in order — so **each concern is its own file**
(`alias.zsh`, `exports.zsh`, `mise.zsh`, `starship.zsh`, tool init like `zoxide`/`fzf`/
`orbstack`/`secretive`, etc.). Add new shell behavior as a new `zsh.d/*.zsh` file rather than
growing an existing one. `.zshrc` is precompiled to `.zshrc.zwc`; the compinit dump is
cached under `$XDG_CACHE_HOME/zsh` and only re-audited daily (see `compinit.zsh`).

**`bin/` holds fzf-driven interactive helpers** (added to PATH via `zsh.d/bin.zsh`):
- `s` / `ss` — ripgrep-all + fzf file search (case-insensitive / case-sensitive), opens the
  hit in `$EDITOR` at the line.
- `f` — like `s` but searches filenames.
- `gd` — fzf over `git status`, difftastic preview, opens selected files.
- `kc` — `kubectl` wrapper (`kc getall` → crds+pods+svc across namespaces).
`$EDITOR` is `code --wait`, and these scripts call `$EDITOR -g file:line` (VS Code syntax).

**Git commits/tags are SSH-signed through Secretive** (a Secure Enclave SSH agent). See
`.config/git/config`: `gpg.format = ssh`, signing program is `.ssh/git-signing-wrapper.sh`,
which resolves the Secretive public key and shells out to `ssh-keygen -Y sign`. The same
Secretive socket is `SSH_AUTH_SOCK` (`zsh.d/secretive.zsh`) and `IdentityAgent`
(`.ssh/config`). Diffs use difftastic (`diff.external = difft`).

## Conventions & gotchas

- Config lives under `.config/` (XDG); it is symlinked as `~/.config`. Prefer adding config
  there over `$HOME`.
- `.config/gcloud`, `.config/op`, and other secret/state dirs are gitignored
  (`.config/.gitignore`) — they appear on disk under the symlinked `~/.config` but are not
  tracked. Don't commit them.
- Shell scripts target both `sh` and macOS's default `zsh`; `bin/gd` uses bash for arrays.
- Machine-specific values belong in `*.local.*` files (`config.local.toml`,
  `~/src/*/.ssh/config.local` via `.ssh/config` Include), never in the shared files.
