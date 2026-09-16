# EscapistsAI — screen agent MVP

A local Windows project for screen capture, calibrated player/HUD perception,
and bounded WASD movement toward nearby screen waypoints. It never reads or
modifies game memory or files. This is an initial movement prototype, not yet
an agent that understands the prison or can escape it.

## Start on this PC

Double-click **Launch.cmd**. It uses the available bundled Python runtime on this
PC (NumPy and Pillow are already present). No installation is needed here.

1. Open a disposable save in **windowed mode**, with default WASD controls.
2. Choose **1** to find the exact game window title, then **2** to capture.
   Switch back to the game during the 10-second delay. Keep it visible and unobscured.
3. Choose **3** to calibrate the saved capture. Drag three rectangles in order:
   your player's sprite; a distinctive static gameplay HUD icon; the playable
   search area. Then click one or two nearby clear-ground waypoints and Save.
4. Choose **4** to observe. Inspect `runs/live/<timestamp>/*-debug.png` and
   `events.jsonl`. A green circle should identify your player. Observation sends no keys.
5. Once the circle is correct, choose **5** for at most 10 seconds of movement.
   Switch to the game during the delay. **Hold F8 to stop**, switch away from the
   game, or create a file named `STOP` in this project. Remove STOP before restarting.

Keep the same resolution, zoom, character appearance, and HUD layout used for
calibration. Recalibrate when these change. Use a small route in a stationary
camera area first. Do not select a distant destination through walls.

## Other PCs / normal Python setup

Python 3.11 or newer, Windows, NumPy and Pillow are required; Tkinter is used for
calibration (included with standard Windows Python). In a terminal here:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e .
.\Run.ps1 demo
.\Run.ps1 windows
.\Run.ps1 capture --title "The Escapists" --delay 10
.\Run.ps1 calibrate runs/capture.png
.\Run.ps1 run --title "The Escapists" --delay 10
.\Run.ps1 run --title "The Escapists" --delay 10 --arm --seconds 10
```

For tests: `python -m unittest discover -s tests -v` with an environment containing
the dependencies. `Run.ps1` chooses `.venv`, then the bundled runtime, then Python
on PATH. All paths for captures/profiles/logs are relative to this project.

## What works and what remains experimental

- Exact window selection, foreground checks, DPI-aware client-region screen capture.
- Appearance matching with an independent fixed HUD check, score threshold and
  ambiguity rejection. Scores are similarity measures, not probabilities.
- Short movement bursts toward local waypoints, route completion, and stopping
  after five observations with no visible player progress.
- Observation mode by default; explicit `--arm` enables input. Only WASD scan
  codes are allowed; each burst is capped at 150 ms and sessions at 120 seconds.
- F8, focus loss, STOP file, stale observations and uncertain perception stop input.
  Keys are released in finally blocks. Abrupt process termination or OS failure
  cannot be covered by Python cleanup guarantees.
- Raw captures, annotated frames, observations, proposed actions, execution
  results and errors are preserved in timestamped run directories.

The template may confuse similar NPCs, reject animation frames, or lose the player
after turning. The HUD check does not understand every menu or overlay. Desktop
capture cannot see behind other windows. Camera scrolling invalidates screen
waypoints and can trigger the no-progress stop. There is no obstacle avoidance,
OCR, NPC recognition, inventory interpretation, schedule logic or escape planner
yet. Mouse actions are intentionally absent from this movement milestone.

Observation mode stops after repeated unchanged player positions because its
policy proposals are not executed; this is a short diagnostic preview.

## Troubleshooting

- **No windows listed:** run Launch.cmd directly on your desktop. A sandbox or
  noninteractive session may see the game process but no desktop windows.
- **Expected one exact title:** use menu option 1 and copy the title exactly.
- **Black capture:** use windowed mode and keep the game visible; no injected
  capture fallback is used.
- **Player not recognized:** inspect the raw image, recapture and select a tight
  sprite crop. Do not lower thresholds blindly; similar NPCs are a known limitation.
- **No visible progress:** inspect for a wall, camera following, wrong controls,
  paused gameplay or rejected input. The agent stops instead of holding the key.
- **Windows rejected input:** run the game and launcher at the same privilege
  level; prefer running both normally rather than as administrator.

## Project layout and development path

`windows.py` owns capture/input; `perception.py` owns image interpretation;
`planning.py` selects local actions; `model.py` defines replaceable interfaces and
observations; `telemetry.py` records evidence; `calibration.py` creates profiles;
`demo.py` exercises a complete simulated perception/action loop.

Next milestones, each validated on recorded frames before enabling controls:

1. Multi-frame directional sprite templates and temporal identity tracking,
   with a labeled frame set including NPC lookalikes, menus and animation.
2. NPC/object detections and UI/OCR components feeding entities, inventory and
   schedule fields on Observation. Unknown values must stay unknown.
3. Camera-motion estimation and persistent world coordinates, then occupancy
   mapping and collision-aware pathfinding. Do not treat screen pixels as a map.
4. Routine/schedule state machines, inventory prerequisites and goal planning.
5. Hierarchical action selection, recovery policies and recorded episode review;
   only then longer prison-escape attempts.

Useful implementation references:
[Windows foreground checks](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getforegroundwindow)
and [SendInput](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput).

## Validation on this machine

See VALIDATION.md for executed checks and live-test limitations.
