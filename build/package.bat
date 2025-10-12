@ECHO ON
DEL *.spec
pyinstaller ..\src\install_wildfire_maps.py ^
    --distpath ..\dist ^
    --collect-all='PIL' ^
    --additional-hooks-dir=. ^
    --onefile --console

ECHO "Smoke-test the executable"
..\dist\install_wildfire_maps.exe -h
