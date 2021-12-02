mkdir build
mkdir build\assets
xcopy /Y assets "build\assets"
xcopy /Y assets\tiny.png build
cd build
python -m nuitka --onefile ..\program.py --windows-icon-from-ico=tiny.png 
cd ..