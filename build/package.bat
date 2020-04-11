REM pip install pypiwin32 pefile 
@ECHO ON
DEL *.spec
pyinstaller ..\src\install_wildfire_maps.py ^
    --distpath ..\dist ^
    --paths ..\lib\ja2-open-toolset ^
    --onefile --console

CD ..
RMDIR dist\wildfire-maps\ /s /q
ROBOCOPY assets\wildfire-maps\ dist\wildfire-maps\ /MIR

COPY README.txt       dist\wildfire-maps\
COPY KNOWN_ISSUES.txt dist\wildfire-maps\
MOVE  dist\install_wildfire_maps.exe dist\wildfire-maps\

CD build

