mkdir build
mkdir build\assets
xcopy /Y assets "build\assets"
cd build
python -m nuitka --onefile ..\program.py 
@REM --windows-icon-from-ico=tiny.png 
cd ..