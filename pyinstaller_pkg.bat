python -m venv venv

call venv\Scripts\activate.bat

pip install -r requirements.dev.txt

pyinstaller -F hpb\main.py --distpath dist\hpb -n hpb
xcopy hpb\etc\ dist\hpb\etc\ /Y /S
xcopy share\ dist\hpb\share\ /Y /S
xcopy README.md dist\hpb\ /Y
xcopy README_cn.md dist\hpb\ /Y

call venv\Scripts\deactivate.bat