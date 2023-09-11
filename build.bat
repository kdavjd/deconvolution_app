@echo off
rem This is deconvolution app build script

set app_name=deconvolution
set venv_dir=venv

rem Populate virtualenv and install dependencies
if not exist %venv_dir%\ (
  echo [INFO] Virtualenv folder '%venv_dir%' not found
  python -m virtualenv %venv_dir%
  call %venv_dir%\Scripts\activate.bat
  python -m pip install -r requirements.txt
)

echo [INFO] Activate virtualenv "%venv_dir%"
call %venv_dir%\Scripts\activate.bat

echo [INFO] Enshure pyinstaller installed
python -m pip install pyinstaller pyinstaller-hooks-contrib
echo [INFO] Build and pack exe file

rem Pack application to exe
pyinstaller --onefile --noconsole --noconfirm --collect-data scienceplots --name %app_name% main.py

echo [INFO] Execution finished

rem Next line optional
pause
