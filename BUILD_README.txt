D2 Runeword Tracker - Windows build

Put these files in the same folder:
- D2RunewordTracker.py
- D2RunewordTracker.spec
- runewords.json
- zod.png
- build_windows.bat

Build:
1. Install Python 3 on Windows.
2. Double-click build_windows.bat.
3. The script installs PyInstaller + Pillow.
4. zod.png is converted to zod.ico automatically.
5. The finished portable app is created at:
   dist\D2RunewordTracker.exe

Data:
- User data: %LOCALAPPDATA%\D2RunewordTracker\user_data.json
- runewords.json and zod.png are bundled inside the executable.

Notes:
- The app uses zod.png as the Tkinter window/taskbar icon.
- Windows EXE icon uses the generated zod.ico.
