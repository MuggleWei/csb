call pyinstaller_pkg.bat

md %UserProfile%\.hpb
xcopy dist\hpb\etc\settings.xml  %UserProfile%\.hpb\ /Y
xcopy dist\hpb\share\ %UserProfile%\.hpb\share\ /Y /S