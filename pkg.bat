python -m venv venv

call venv\Scripts\activate.bat

pip install -r requirements.dev.txt

pyinstaller -F src\main.py --distpath dist\lpb -n lpb
xcopy etc\ dist\lpb\etc\ /Y /S
xcopy scripts\ dist\lpb\scripts\ /Y /S
xcopy README.md dist\lpb\README.md /Y /F
xcopy README_cn.md dist\lpb\README_cn.md /Y /F

call venv\Scripts\deactivate.bat