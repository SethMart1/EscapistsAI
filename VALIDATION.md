# Validation — 2026-09-16

Executed with the bundled Python runtime on this PC:

- `python -m unittest discover -s tests -v`: **15 tests passed**.
- `Run.ps1 demo`: **two waypoints reached**, 31 recorded frames.
- Inspected a saved debug image: detected position and action annotation rendered.
- Win32 INPUT structure size verified for the current architecture.
- `Run.ps1 windows`: the execution environment returns no visible windows and
  a null foreground handle, even though the game process is running.

Tests cover synthetic player localization, duplicate-player ambiguity, missing
HUD/player, resolution changes, blocked movement, unknown state, route completion,
dry-run behavior, stale observations, F8, invalid actions and key release on
mid-action focus loss. Input tests use a mocked sender: **no live keystrokes were
sent to the game**.

Demo evidence is in `runs/demo/20260916-000151/`: raw PNGs, annotated PNGs and
events.jsonl. Runtime output directories are intentionally excluded from Git.

The game installation and running TheEscapists_eur process were confirmed.
Actual game capture, calibration, animation robustness and movement remain
unverified because this session cannot access desktop windows. Launch.cmd must
be run directly on the interactive desktop to perform those checks.

The automated demo validates the software loop, not recognition accuracy on
The Escapists. Real captured frames are the next required validation dataset.
