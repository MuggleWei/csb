python -m venv venv

call venv\Scripts\activate.bat

pip install -r requirements.dev.txt

pyinstaller -F src\main.py --distpath dist\hpb -n hpb
xcopy etc\ dist\hpb\etc\ /Y /S
xcopy scripts\ dist\hpb\scripts\ /Y /S
xcopy README.md dist\hpb\README.md /Y /F
xcopy README_cn.md dist\hpb\README_cn.md /Y /F

call venv\Scripts\deactivate.bat
