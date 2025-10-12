@ECHO ON
DEL *.spec
pyinstaller ..\src\install_wildfire_maps.py ^
    --distpath ..\dist ^
    --hidden-import=PIL ^
    --hidden-import=Pillow ^
    --collect-all='PIL' ^
    --onefile --console

ECHO "Smoke-test the executable"
..\dist\install_wildfire_maps.exe -h
