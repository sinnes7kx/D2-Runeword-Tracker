<div align="center">

# ⚔️ D2 Runeword Tracker

### A lightweight Runeword tracker for Diablo II: Resurrected

Track completed Runewords, manage your rune inventory, see what you can craft, and keep your Chronicle progress in one simple desktop app.

<br>

[![Windows](https://img.shields.io/badge/Windows-10%20%7C%2011-0078D6?logo=windows\&logoColor=white)](https://github.com/sinnes7kx/D2-Runeword-Tracker/releases)
[![Python](https://img.shields.io/badge/Python-Tkinter-3776AB?logo=python\&logoColor=white)](https://www.python.org/)
[![GitHub release](https://img.shields.io/github/v/release/sinnes7kx/D2-Runeword-Tracker?include_prereleases\&label=Release)](https://github.com/sinnes7kx/D2-Runeword-Tracker/releases)
[![GitHub downloads](https://img.shields.io/github/downloads/sinnes7kx/D2-Runeword-Tracker/total?label=Downloads)](https://github.com/sinnes7kx/D2-Runeword-Tracker/releases)
[![PayPal](https://img.shields.io/badge/Donate-PayPal-00457C?logo=paypal\&logoColor=white)](https://www.paypal.com/ncp/payment/KUM5TR7ETF4QJ)

<br>

[**⬇ Download Latest Release**](https://github.com/sinnes7kx/D2-Runeword-Tracker/releases/latest)
  •  
[**🐛 Report an Issue**](https://github.com/sinnes7kx/D2-Runeword-Tracker/issues)
  •  
[**☕ Donate**](https://www.paypal.com/ncp/payment/KUM5TR7ETF4QJ)

</div>

---

## 📖 About

**D2 Runeword Tracker** is a small desktop application for tracking Runewords in **Diablo II: Resurrected**.

It was built for players working through their Runeword collection or Chronicle who want a fast way to see:

* which Runewords are completed
* which Runewords are still missing
* which ones can be crafted with their current rune inventory
* which Runewords are only one rune away
* detailed Runeword stats and variable rolls

Everything is stored **locally on your computer**. No account, cloud service, or internet connection is required to use the tracker.

---

## ✨ Features

<table>
<tr>
<td width="50%">

### ✅ Runeword Checklist

Mark Runewords as completed and track your overall progress.

The tracker automatically shows:

* Completion percentage
* Runewords remaining
* Currently craftable Runewords

</td>
<td width="50%">

### 💎 Rune Inventory

Enter the number of each rune you currently own.

The tracker automatically determines which Runewords you can craft based on your inventory.

</td>
</tr>

<tr>
<td width="50%">

### 🔎 Search & Filters

Quickly find Runewords by:

* Name
* Rune
* Base
* Required level

Available filters include:

* All
* Missing
* Completed
* Can Craft
* Missing 1 Rune
* Favorites

</td>
<td width="50%">

### ⭐ Favorites

Mark important Runewords as favorites for quick access.

Useful for tracking Runewords you're currently farming toward.

</td>
</tr>

<tr>
<td width="50%">

### 📊 Detailed Stats

Open the details window using the stats button or by **double-clicking a Runeword**.

View:

* Rune order
* Socket count
* Compatible bases
* Required level
* Craftable copies
* Full Runeword stats

</td>
<td width="50%">

### 🎲 Variable Roll Highlighting

Stats that can roll within a range are highlighted separately.

For example:

```text
+25 to 35% Faster Cast Rate
+200 to 260% Enhanced Damage
```

This makes variable Runeword rolls easier to identify.

</td>
</tr>
</table>

---

## 🖥️ Screenshot

<div align="center">

<!-- Replace this with your screenshot when you add one to the repository -->

<img src="screenshot.png" alt="D2 Runeword Tracker Screenshot" width="800">

</div>

> Add a screenshot named `screenshot.png` to the root of the repository for the preview above to appear.

---

## 🚀 Installation

### Recommended — Windows Release

1. Go to the [**Releases**](https://github.com/sinnes7kx/D2-Runeword-Tracker/releases) page.
2. Download the latest Windows `.exe`.
3. Start **D2RunewordTracker.exe**.
4. That's it.

Python is **not required** when using the packaged Windows release.

> Windows SmartScreen may display a warning for unsigned applications downloaded from GitHub. This can happen with independently distributed applications that do not use a commercial code-signing certificate.

---

## 💾 Where is my progress saved?

Your inventory, favorites, and completed Runewords are stored separately from the application.

On Windows:

```text
%LOCALAPPDATA%\D2RunewordTracker\user_data.json
```

Usually this resolves to:

```text
C:\Users\YourName\AppData\Local\D2RunewordTracker\user_data.json
```

This means updating or replacing the `.exe` should not remove your progress.

### What is stored?

```text
Rune inventory
Completed Runewords
Favorite Runewords
```

Your data stays on your own computer.

---

## 🎮 How to Use

### 1. Add your runes

Open the menu:

```text
☰ → Rune Inventory
```

Enter how many of each rune you currently own.

---

### 2. Find craftable Runewords

Select:

```text
Can craft
```

from the filter menu.

The tracker compares every Runeword against your current inventory.

---

### 3. Check Runeword stats

Either:

* click the **…** button
* or **double-click the Runeword**

to open its detailed stats.

---

### 4. Mark it complete

Press the **✔** button after creating a Runeword.

Your completion percentage will update automatically.

---

## 🔍 Sorting

Runewords can currently be sorted by:

| Sort                | Description                            |
| ------------------- | -------------------------------------- |
| **Default**         | Incomplete Runewords first             |
| **Name**            | Alphabetical order                     |
| **Level**           | Required character level               |
| **Craftable first** | Runewords you can currently make first |

---

## 📦 Application Data

The Runeword database is bundled directly with the application:

```text
runewords.json
```

User progress is stored independently in AppData.

This allows the distributed Windows `.exe` to remain self-contained while keeping user saves persistent between updates.

---

## 🛠️ Running from Source

If you want to run the Python version instead:

### Requirements

* Python 3.10+
* Tkinter

Clone the repository:

```bash
git clone https://github.com/sinnes7kx/D2-Runeword-Tracker.git
cd D2-Runeword-Tracker
```

Run:

```bash
python D2RunewordTracker.py
```

---

## 🔨 Building the Windows Executable

The project can be packaged using **PyInstaller**.

Install the required build tools:

```bash
pip install pyinstaller pillow
```

Then build using the included specification/build script.

The resulting executable will be placed in:

```text
dist/D2RunewordTracker.exe
```

The following application resources are bundled with the executable:

```text
runewords.json
zod.png
```

`zod.png` is used for the application icon.

---

## 📁 Project Structure

```text
D2-Runeword-Tracker/
│
├── D2RunewordTracker.py
├── D2RunewordTracker.spec
├── runewords.json
├── zod.png
├── build_windows.bat
├── README.md
└── LICENSE
```

---

## 💖 Support the Project

If you enjoy the tracker and want to support development:

<div align="center">

### [☕ Donate via PayPal](https://www.paypal.com/ncp/payment/KUM5TR7ETF4QJ)

Every donation is appreciated, but the application remains free to use.

</div>

---

## 🐛 Bugs & Suggestions

Found a bug or have an idea for a feature?

[**Open an issue on GitHub →**](https://github.com/sinnes7kx/D2-Runeword-Tracker/issues)

Ideas and contributions are welcome.

## 📚 Runeword Data

Runeword information is stored in the project's `runewords.json` database.

Data has been compiled using publicly available Diablo II Runeword information, including references from:

* [diablo2.io](https://diablo2.io/runewords/)

---

## ⚠️ Disclaimer

D2 Runeword Tracker is an independent fan-made project.

It is **not affiliated with, endorsed by, or associated with Blizzard Entertainment**.

Diablo, Diablo II, Diablo II: Resurrected, and related names and trademarks belong to their respective owners.

This application does not modify the game client or game files.

---

<div align="center">

### ⚔️ D2 Runeword Tracker

**Track the runes. Forge the words. Complete the Chronicle.**

<br>

Made for the Diablo II community.

[Download](https://github.com/sinnes7kx/D2-Runeword-Tracker/releases/latest)
•
[Issues](https://github.com/sinnes7kx/D2-Runeword-Tracker/issues)
•
[Donate](https://www.paypal.com/ncp/payment/KUM5TR7ETF4QJ)

</div>
