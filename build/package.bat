REM pip install pypiwin32 pefile 
@ECHO ON
DEL *.spec
pyinstaller ..\src\install_wildfire_maps.py ^
    --distpath ..\dist ^
    --paths ..\lib\ja2-open-toolset ^
    --onefile --console
