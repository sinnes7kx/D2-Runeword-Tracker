<div align="center">

⚔️ D2 Runeword Tracker
A lightweight Runeword tracker for Diablo II: Resurrected
Track completed Runewords, manage your rune inventory, and see exactly which runes you still need to finish your collection or Chronicle.

 
 
 
 
 

⬇ Download Latest Release
  •  
🐛 Report an Issue
  •  
☕ Donate
</div>

📖 About
D2 Runeword Tracker is a small desktop application for tracking Runewords in Diablo II: Resurrected.
Keep a checklist of completed Runewords, find recipes you can craft, and plan your rune farming with a combined total for every Runeword you still need.
Everything is stored locally on your computer. No account or internet connection is required to use the tracker. Inventory and completion are entered manually; the app does not read your game saves or sync with the game.
✨ Features
Feature	What it does
✅ Runeword checklist	Mark Runewords completed and track completion percentage, remaining entries, and currently craftable recipes.
💎 Rune inventory	Enter how many of each rune you own and see which recipes your inventory covers.
🧮 Rune totals	View required, owned, and still-needed quantities for each rune across all uncompleted Runewords.
🔎 Search and filters	Search by name, rune, base, or required level. Filter by completion, craftability, missing runes, or favorites.
⭐ Favorites	Save the Runewords you want to find quickly or farm toward next.
📊 Detailed stats	View rune order, sockets, compatible bases, required level, craftable copies, and full stats.
🎲 Variable rolls	Highlight variable stats when they are identified in the database.
🌙 Dark interface	Dark tables, headers, dropdowns, menus, and scrollbars, with gold accents and colored rune availability.
💾 Automatic saving	Keep inventory, favorites, and checklist progress between sessions and application updates.


🧮 Runes for Missing Runewords
Click Rune totals, or open ☰ → Runes for Missing Runewords.
The window counts the runes needed to make one copy of every uncompleted Runeword.
Column	Meaning
Rune	The rune type, listed in rune order.
Required	Total copies needed across all uncompleted Runewords.
Owned	Copies recorded in your rune inventory.
Still needed	Required minus owned, with a minimum of zero.


The summary shows how many Runewords remain, the total number of runes required, and how many additional runes you need across how many rune types.
- Repeated runes in a recipe are counted individually.
- Your inventory is deducted once from the combined requirements, so the same rune cannot cover multiple recipes at once.
- Totals include all uncompleted Runewords, regardless of the current search or filter.
- The window updates automatically when you change completion status or commit an inventory change.
- Orange rows indicate a shortage; green rows indicate enough runes for that type.
- Use Edit inventory to adjust your rune counts directly from this window.
For example, if your remaining recipes require 3 Ber in total and you own 1 Ber, the table shows 2 still needed.
These are direct rune requirements. Horadric Cube upgrades and gem costs are not included.
🖥️ Screenshot
<div align="center">

<img src="screenshot.png" alt="D2 Runeword Tracker dark interface" width="800">

</div>

<!-- Add an up-to-date screenshot.png to the repository root. -->

🚀 Installation
1. Open the Releases page.
2. Download the latest Windows .exe.
3. Start D2RunewordTracker.exe.
Python is not required for the packaged Windows release. The Runeword database is bundled into the executable when built using the command below.
🎮 How to Use
1. Add your runes
Open ☰ → Rune Inventory and enter the number of each rune you own. Press Enter or move out of the field to save a typed value. The spinner arrows also save changes.
2. Find recipes you can craft
Select Can craft from the filter menu. Each recipe is checked individually against your current inventory.
Several recipes may use the same runes, so being listed as craftable does not mean you can make all of them together. Use Rune totals to see the combined requirements for your unfinished collection.
3. Check stats
Click … or double-click a Runeword to open its details. You can see rune order, bases, socket count, required level, craftable copies, missing runes, and stats.
4. Mark a Runeword complete
Click ✔ after creating a Runeword. Click ↩ to mark it incomplete again.
Marking a Runeword completed does not deduct runes from your inventory. Update your inventory after crafting to keep availability and totals accurate.
5. Plan your next rune hunt
Open Rune totals to see exactly how many more runes of each type you need for the remaining Runewords. Marking recipes completed removes their requirements from this window.
6. Keep favorites handy
Click ☆ to favorite a Runeword, then select Favorites to find it quickly. Click ★ to remove it from favorites.
🔎 Filters and Sorting
Filter	Shows
All	Every Runeword.
Missing	Runewords not marked completed.
Completed	Runewords marked completed.
Can craft	Recipes covered by your current rune inventory, including completed entries.
Missing 1 rune	Recipes short of exactly one rune copy, including completed entries.
Favorites	Runewords you have starred.


Missing refers to checklist completion. A missing Runeword can still be craftable with the runes you own.
Sort	Order
Default	Uncompleted first, then required level and name.
Name	Alphabetical.
Level	Required character level.
Craftable first	Craftable recipes first, then uncompleted entries and name within each group.


💾 Where Is My Progress Saved?
Inventory, favorites, and completed Runewords are stored separately from the application.
On Windows:
%LOCALAPPDATA%\D2RunewordTracker\user_data.json
Usually:
C:\Users\YourName\AppData\Local\D2RunewordTracker\user_data.json
Replacing or updating the executable keeps this save file intact. To back up your progress, copy user_data.json somewhere safe while the tracker is closed.
☰ → Reset completed clears the completion checklist after confirmation. It keeps inventory and favorites.
🛠️ Running from Source
You need Python with Tkinter installed. The application uses Python's standard library; no additional runtime packages are required.
git clone https://github.com/sinnes7kx/D2-Runeword-Tracker.git
cd D2-Runeword-Tracker
python D2RunewordTracker.py
Keep runewords.json beside D2RunewordTracker.py. If available, place zod.png in the same folder for the application window icon.
🔨 Building the Windows Executable
Run these commands on Windows, from the project folder.
Install or update PyInstaller:
py -m pip install --upgrade pyinstaller
Build a single executable with the database bundled:
py -m PyInstaller --onefile --windowed --add-data "runewords.json:." D2RunewordTracker.py
If zod.png is available, include the window icon as well:
py -m PyInstaller --onefile --windowed --add-data "runewords.json:." --add-data "zod.png:." D2RunewordTracker.py
The executable is created at:
dist\D2RunewordTracker.exe
zod.png supplies the running application's window icon. To set the executable's icon in File Explorer as well, add --icon "zod.ico" to your build command if you have that .ico file.
Personal user_data.json is not bundled with the release. Each user keeps their own progress separately.
📦 Main Files
File	Purpose
D2RunewordTracker.py	Desktop application.
runewords.json	Runeword recipes, bases, levels, and stats.
zod.png	Optional application window icon.
screenshot.png	Screenshot shown in this README.
README.md	Project documentation.


📚 Runeword Data
Runeword information is stored in the project's runewords.json database. Data has been compiled using publicly available Diablo II Runeword information, including references from diablo2.io.
Displayed recipes and stats depend on the bundled database. If you spot an incorrect entry, please open an issue with the Runeword name and the correction.
💖 Support the Project
If you enjoy the tracker and want to support development:
☕ Donate via PayPal
Every donation is appreciated, and the application remains free to use.
🐛 Bugs and Suggestions
Found a bug or have an idea for a feature? Open an issue on GitHub →
For bugs, include what you were doing, what happened, and any error message or screenshot. Ideas and contributions are welcome.
⚠️ Disclaimer
D2 Runeword Tracker is an independent fan-made project. It is not affiliated with, endorsed by, or associated with Blizzard Entertainment.
Diablo, Diablo II, Diablo II: Resurrected, and related names and trademarks belong to their respective owners.
This application does not modify the game client or game files.
<div align="center">

⚔️ D2 Runeword Tracker
Track the runes. Forge the words. Complete the Chronicle.
Made for the Diablo II community.
Download
• Issues
• Donate
</div>
