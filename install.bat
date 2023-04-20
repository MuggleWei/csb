python -m pip install --user -e .

md %UserProfile%\.hpb
xcopy etc\settings.xml  %UserProfile%\.hpb\ /Y
xcopy share\ %UserProfile%\.hpb\share\ /Y /S
