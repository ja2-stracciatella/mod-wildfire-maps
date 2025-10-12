@ECHO ON
DEL *.spec
pyinstaller ..\src\install_wildfire_maps.py ^
    --distpath ..\dist ^
    --hidden-import='pkg_resources.py2_warn' ^
    --hidden-import='PIL._imaging' ^
    --collect-all='PIL' ^
    --paths ..\lib\ja2-open-toolset ^
    --onefile --console

ECHO "Smoke-test the executable"
..\dist\install_wildfire_maps.exe -h
