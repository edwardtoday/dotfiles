# Hammerspoon

This directory is the shared Hammerspoon runtime for the two Macs.

- `common/` contains shared handoff and presence state machines.
- `hosts.lua` contains tracked host-specific display/input settings.
- `modules/` contains existing shared integrations such as wired route management.
- `~/.hammerspoon-host` selects `mbp` or `m4mini` on each machine.
- `~/.hammerspoon-local.lua` contains machine-local values such as the presence token and is intentionally outside the repository.

The repository root is linked to `~/.hammerspoon` on each Mac. Reload Hammerspoon after changing the configuration.
