python -m pip install .

md %UserProfile%\.hpb
xcopy etc\settings.xml  %UserProfile%\.hpb\ /Y
xcopy share\ %UserProfile%\.hpb\share\ /Y /S
