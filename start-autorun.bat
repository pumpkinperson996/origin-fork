@echo off
cd /d C:\ZZZ-OD\ZZZ-autorun
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath 'C:\ZZZ-OD\.tools\AutoHotkey-v1.1.37.02\AutoHotkeyU64.exe' -ArgumentList 'C:\ZZZ-OD\ZZZ-autorun\OneDragon_FINAL_Restart_90min.ahk' -Verb RunAs"
