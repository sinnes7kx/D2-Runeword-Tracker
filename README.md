# ⚔️ D2 Runeword Tracker

**A lightweight Windows runeword tracker for Diablo II: Resurrected.**

Track completed runewords, manage your rune inventory, see what you can craft, and plan the runes you still need for your collection or Chronicle.

[![Latest Release](https://img.shields.io/github/v/release/sinnes7kx/D2-Runeword-Tracker?label=Latest%20release)](https://github.com/sinnes7kx/D2-Runeword-Tracker/releases/latest)
[![Download for Windows](https://img.shields.io/badge/Download-Windows-272727?logo=windows)](https://github.com/sinnes7kx/D2-Runeword-Tracker/releases/latest)
[![Report an issue](https://img.shields.io/badge/Report-an%20issue-c9a85c)](https://github.com/sinnes7kx/D2-Runeword-Tracker/issues)

## ✨ Features

- **Runeword checklist:** Mark recipes complete and track overall progress.
- **Rune inventory:** Record the number of each rune you own and identify craftable recipes.
- **Automatic rune deductions (v1.3):** When you complete a runeword using runes recorded in your inventory, the required runes are deducted. Repeated runes are counted individually.
- **30-second refund window (v1.3):** Undo a completion within 30 seconds to return the runes deducted for that completion. After the window expires, you may still uncheck the runeword, but spent runes are not automatically refunded.
- **Runewords you already owned:** You can mark a runeword complete without deducting inventory if you don't have its required runes recorded.
- **Rune totals:** See required, owned, and missing rune counts for all unfinished runewords together.
- **Search and filters:** Search by runeword, rune, base, or required level. Filter completed, missing, craftable, one-rune-away, and favorite entries.
- **Detailed recipes:** View rune order, sockets, bases, level requirements, craftable copies, stats, and highlighted variable rolls where available.
- **Fast, near-black interface (v1.3):** Dark charcoal/black UI, restrained gold accents, smoother hover and press feedback, and faster completion/restoration updates.
- **Update notifications (v1.3):** Checks published GitHub releases for newer versions and offers a link to download them. Use **☰ → Check for updates** to check manually.
- **Local automatic saving:** Keeps your rune inventory, checklist, favorites, and applicable refund information between sessions.

The tracker **does not read Diablo II save files or communicate with the game**. You enter your rune inventory and completion status manually. An internet connection is only needed to check for/download updates.

## 🚀 Download and install

1. Go to the **[latest GitHub Release](https://github.com/sinnes7kx/D2-Runeword-Tracker/releases/latest)**.
2. Download the Windows `.exe` or ZIP asset provided under **Assets**.
3. If you downloaded a ZIP, extract it before running the application.
4. Launch `D2RunewordTracker.exe`.

The packaged Windows executable does not require Python to be installed. Download the release asset, **not** GitHub's automatically generated “Source code” ZIP, if you just want to run the program.

## 🎮 How to use

### Manage your runes

Open **☰ → Rune Inventory**. Enter the quantity of each rune you own; changes save locally.

### Find and complete a runeword

Use the **Can craft** filter to see which recipes are covered by your recorded rune inventory. Click the **✔** button beside a runeword you have crafted. In v1.3, the required runes are deducted when available and you confirm completion.

If you make a mistake, click **↩** within **30 seconds** to restore the deducted runes. The undo period is based on the original completion time, even if you close and reopen the app. After 30 seconds, unchecking removes its completed status but **does not return spent runes**.

If you already have a completed runeword but did not enter the runes used to craft it, you can mark it completed without deducting inventory.

### See what is missing

Click **Rune totals** (or **☰ → Runes for Missing Runewords**) to see how many runes are needed to make one copy of every unfinished runeword. Inventory is deducted once from the combined requirements, rather than being reused across different recipes. These totals use direct runes only; cube upgrades are not included.

### Favorites, details, and search

Click **☆** to favorite a runeword. Click **…** or double-click a row to inspect its details. Search by name, rune, item base, or required level; click outside the search box to remove focus without clearing your search.

## 🔔 Updates

Starting with v1.3, the application can check the latest published release at this repository. If a newer version exists, it displays an update notification and a link to the GitHub release page. You can also check from **☰ → Check for updates**.

The app **does not automatically install or replace** its own executable. Download and launch the newer release manually. The update checker does not affect normal offline use.

## 💾 Where is my progress saved?

On Windows, your data is stored outside the executable:

```text
%LOCALAPPDATA%\D2RunewordTracker\user_data.json
```

That file contains your rune counts, favorites, completed runewords, and v1.3 completion/refund data. Replacing the executable normally leaves your saved progress intact. For backups or transfers, close the program and copy `user_data.json` to a safe location.

**Do not upload your personal `user_data.json` to a public GitHub repository.**

## 🖥️ Screenshots

Screenshots of the actual running application can be added here when available.

<!-- Example after uploading an actual screenshot:
![Main interface](assets/screenshots/main.png)
-->

## 🛠️ Run from Python source

The app uses Python and Tkinter (normally bundled with standard Python Windows installations). It requires no third-party Python packages at runtime.

```bash
git clone https://github.com/sinnes7kx/D2-Runeword-Tracker.git
cd D2-Runeword-Tracker
python D2RunewordTracker.py
```

Keep `runewords.json` alongside the Python script. If you have `zod.png`, put it there for the application window icon.

## 🔨 Build a Windows executable

Install PyInstaller:

```bat
py -m pip install --upgrade pyinstaller
```

Then, from the project folder, run the following if both Zod icon files are present:

```bat
py -m PyInstaller --onefile --windowed --clean --noconfirm --name "D2RunewordTracker" --icon "zod.ico" --add-data "runewords.json;." --add-data "zod.png;." "D2RunewordTracker.py"
```

The result will be in `dist\D2RunewordTracker.exe`. `zod.ico` sets the executable's Windows icon; `zod.png` sets the running application's window icon. Neither personal save data nor `user_data.json` should be bundled.

## 🐛 Bugs and suggestions

Found an issue, incorrect rune recipe, or have a feature request? **[Open an issue](https://github.com/sinnes7kx/D2-Runeword-Tracker/issues)** with steps to reproduce, the program version, and screenshots if relevant.

## 💖 Support the project

If the tracker is useful to you, you can [donate via PayPal](https://www.paypal.com/donate/?hosted_button_id=H5QKDWLF92MXN). Donations are optional; the application is free to use.

## ⚠️ Disclaimer

D2 Runeword Tracker is an independent fan-made utility, not affiliated with or endorsed by Blizzard Entertainment. Diablo, Diablo II, Diablo II: Resurrected, and related names and trademarks belong to their respective owners. This tracker does not modify game files.

---

**Track the runes. Forge the words. Complete the Chronicle.**
