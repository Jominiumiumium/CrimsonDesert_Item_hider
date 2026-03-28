# Crimson Desert Item Visibility Changer
Thanks to lazorr410 for the unpacking tool!


My gui/tool is 110% Vibe coded.


A patcher to change item visibility in Crimson Desert.

## Overview

This tool lets you edit XML files to control the visibility of equipment on your character in Crimson Desert. It's especially useful if you want to hide certain items—like shields, bows, etc.—from your character's back while still making them visible when in use.

## Features

- Hide shields, bows, and more from your character's back
- Equipment remains visible during active use
- **Smart Discovery**: Automatically scans all connected drives (C: to Z:) to find your game installation in common Steam or standalone paths.
- **Auto-Backup**: Creates a `.bak` file for any modified PAZ archives, allowing for easy restoration to the original state.

## Installation & How to use

1. Clone or download this repository.
2. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the editor:
   ```bash
   python xml_kliff_editor.py
   ```
4. The tool will attempt to find the game automatically. If it fails, it will ask you to select the game folder (the one containing the `0009` folder).
5. Select the items you wish to hide and click **"Apply Changes"**.
