@echo off
setlocal
cd /d %~dp0

if not exist zod.png (
    echo.
    echo ERROR: zod.png is missing from this folder.
    pause
    exit /b 1
)

py -m pip install --upgrade pyinstaller pillow
if errorlevel 1 goto :error

py -c "from PIL import Image; im=Image.open('zod.png').convert('RGBA'); im.save('zod.ico', sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])"
if errorlevel 1 goto :error

py -m PyInstaller --noconfirm --clean D2RunewordTracker.spec
if errorlevel 1 goto :error

echo.
echo Build complete: dist\D2RunewordTracker.exe
echo EXE icon: zod.png -^> zod.ico
pause
exit /b 0

:error
echo.
echo Build failed. See the errors above.
pause
exit /b 1
