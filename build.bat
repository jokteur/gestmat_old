mkdir build
mkdir build\assets
xcopy /Y assets "build\assets"
xcopy /Y assets\tiny.png build
cd build
python -m nuitka --onefile --windows-company-name=HFR --windows-product-name=gestmat --windows-product-version=0.1 --windows-file-description="Gestion materiel"  ..\program.py --windows-icon-from-ico=tiny.png 
cd ..
@REM xcopy /Y assets "build\program.dist\assets"
@REM xcopy /Y sauvegardes "build\program.dist\sauvegardes"