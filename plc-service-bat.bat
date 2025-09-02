@echo off
REM This batch file helps install and manage the PLC Backup Service

echo PLC Backup Service Manager
echo =========================
echo.

REM Activate the virtual environment
set VENV_PATH=E:\pythonProjects\automatedBackups\.venv
call "%VENV_PATH%\Scripts\activate.bat"

echo Using Python from: %PYTHON%
where python

REM Check command argument
if "%1"=="" goto usage
if "%1"=="install" goto install
if "%1"=="uninstall" goto uninstall
if "%1"=="start" goto start
if "%1"=="stop" goto stop
if "%1"=="restart" goto restart
if "%1"=="debug" goto debug
goto usage

:install
echo Installing PLC Backup Service...
echo.
REM Ensure we're running with admin privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Administrator privileges required.
    echo Please run this script as Administrator.
    goto end
)
python PLCBackupService.py --startup auto install
if %errorlevel% equ 0 (
    echo Service installed successfully.
) else (
    echo Service installation failed with error code %errorlevel%.
)
goto end

:uninstall
echo Removing PLC Backup Service...
echo.
REM Ensure we're running with admin privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Administrator privileges required.
    echo Please run this script as Administrator.
    goto end
)
python PLCBackupService.py remove
goto end

:start
echo Starting PLC Backup Service...
echo.
net start PLCBackupService
goto end

:stop
echo Stopping PLC Backup Service...
echo.
net stop PLCBackupService
goto end

:restart
echo Restarting PLC Backup Service...
echo.
net stop PLCBackupService
timeout /t 2 /nobreak >nul
net start PLCBackupService
goto end

:debug
echo Running in debug mode...
echo.
python PLCBackupService.py debug
goto end

:usage
echo Usage: service.bat [command]
echo.
echo Commands:
echo   install   - Install the service (requires admin privileges)
echo   uninstall - Uninstall the service (requires admin privileges)
echo   start     - Start the service
echo   stop      - Stop the service
echo   restart   - Restart the service
echo   debug     - Run the service in debug mode (foreground)
echo.

:end
echo.
REM Deactivate the virtual environment
call deactivate
