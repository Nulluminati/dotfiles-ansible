# CLAUDE.md

## MANDATORY: Use td for Task Management

You must run td usage --new-session at conversation start (or after /clear) to see current work.
Use td usage -q for subsequent reads.

Ansible + GNU Stow dotfiles management for Fedora Linux (macOS partial).

## WHY

Reproducible development environment setup across machines. Ansible handles system packages and configuration; Stow symlinks dotfiles to home directory.

## WHAT

```
bootstrap.yml    # Main playbook - imports all roles with tags
bin/             # Setup scripts
hosts            # Ansible inventory (localhost)
roles/           # Ansible roles: uv, llm, cli, ai_tooling, stow, fonts, sublime, nvidia
dotfiles/
  fedora/        # Fedora-specific configs
  shared/        # Cross-platform configs
  mac/           # macOS-specific (partial)
secrets.example.yml  # Template for secrets (copy to secrets.yml)
secrets.yml      # API keys and sensitive config (gitignored)
```

## HOW

```bash
# Full bootstrap
./bin/setup

# Show help
./bin/setup -h

# Specific roles
./bin/setup -t "fonts,cli"

# Dry-run (preview changes without applying):
./bin/setup -t "cli" --check
# Or run ansible directly:
ansible-playbook bootstrap.yml --extra-vars @secrets.yml -i hosts --check --tags "cli" --ask-become-pass
```

When modifying roles:
- Each role follows `tasks/main.yml` and `defaults/main.yml` structure
- Platform-specific tasks go in `tasks/fedora.yml` or `tasks/mac.yml`
- See `bootstrap.yml:1-38` for available role tags

For secrets, reference `secrets.example.yml` (never commit `secrets.yml`).

## Stow Management

Dotfiles are symlinked via GNU Stow, but **managed through Ansible** (not run manually). The `stow` role:
1. Installs stow via package manager (dnf/homebrew)
2. Auto-discovers all directories under `dotfiles/fedora/` or `dotfiles/mac/`
3. Runs `stow -t ~ <package>` for each directory automatically

This means adding a new dotfile package only requires creating the directory - Ansible will stow it on the next run.
