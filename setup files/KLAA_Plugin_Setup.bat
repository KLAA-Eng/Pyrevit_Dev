@echo off
setlocal EnableDelayedExpansion
title KLAA pyRevit Setup

REM ============================================================
REM  CONFIGURATION
REM ============================================================
set LOG_FILE=%TEMP%\KLAA_pyrevit_setup.log

REM --- SET EXTENSIONS JSON LOCATIONS FOR ANY USER INSTALL ---
set EXT_JSON=
set SEARCH_PATHS=^
    "%APPDATA%\pyRevit-Master\extensions\extensions.json" ^
    "%APPDATA%\pyRevit\extensions\extensions.json" ^
    "%LOCALAPPDATA%\pyRevit-Master\extensions\extensions.json" ^
    "%LOCALAPPDATA%\pyRevit\extensions\extensions.json" ^
    "%PROGRAMDATA%\pyRevit\extensions\extensions.json"

REM --- KNOWN PYREVIT CLI LOCATIONS ---
set PYREVIT_CLI=
set CLI_PATHS=^
    "%LOCALAPPDATA%\pyRevit-Master\bin\pyrevit.exe" ^
    "%LOCALAPPDATA%\pyRevit\bin\pyrevit.exe" ^
    "%PROGRAMDATA%\pyRevit\bin\pyrevit.exe" ^
    "%PROGRAMFILES%\pyRevit\bin\pyrevit.exe"

echo ============================================================ > "%LOG_FILE%"
echo KLAA pyRevit Setup Log >> "%LOG_FILE%"
echo Started: %DATE% %TIME% >> "%LOG_FILE%"
echo User: %USERNAME% >> "%LOG_FILE%"
echo Machine: %COMPUTERNAME% >> "%LOG_FILE%"
echo ============================================================ >> "%LOG_FILE%"

echo.
echo  KLAA pyRevit Setup
echo  ==================
echo.

REM ============================================================
REM  STEP 1 - FIND PYREVIT CLI
REM ============================================================
echo [1/3] Locating pyRevit CLI...

where pyrevit >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYREVIT_CLI=pyrevit
    echo       Found on system PATH
    echo       Found on system PATH >> "%LOG_FILE%"
    goto CLI_FOUND
)

for %%P in (%CLI_PATHS%) do (
    if exist %%P (
        set PYREVIT_CLI=%%P
        echo       Found at %%P
        echo       Found at %%P >> "%LOG_FILE%"
        goto CLI_FOUND
    )
)

echo [ERROR] pyRevit CLI not found. >> "%LOG_FILE%"
echo  ERROR: pyRevit CLI not found.
echo  Install pyRevit first: https://github.com/pyrevitlabs/pyRevit/releases
goto FAILURE

:CLI_FOUND

REM ============================================================
REM  STEP 2 - LOCATE EXTENSIONS.JSON IN pyRevit DIRECTORY
REM ============================================================
echo [2/3] Locating extensions.json...

for %%P in (%SEARCH_PATHS%) do (
    if exist %%P (
        set EXT_JSON=%%P
        echo       Found at %%P
        echo       Found at %%P >> "%LOG_FILE%"
        goto JSON_FOUND
    )
)

echo [ERROR] extensions.json not found. >> "%LOG_FILE%"
echo  ERROR: Could not locate pyRevit extensions.json
echo  Check that pyRevit is fully installed.
goto FAILURE

:JSON_FOUND

REM ============================================================
REM  STEP 3 - RUN POWERSHELL SCRIPT TO INJECT KLAA EXTENSION OBJECT
REM ============================================================
echo [3/3] Adding KL^&A Tools to extensions.json...

set EXT_JSON_CLEAN=%EXT_JSON:"=%

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0inject_extension.ps1" -JsonPath "%EXT_JSON_CLEAN%" >> "%LOG_FILE%" 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to update extensions.json >> "%LOG_FILE%"
    echo  ERROR: Failed to update extensions.json
    echo  Check the log at: %LOG_FILE%
    goto FAILURE
)
echo       OK: extensions.json updated >> "%LOG_FILE%"
echo       OK: extensions.json updated

REM ============================================================
REM  SUCCESS
REM ============================================================
echo. >> "%LOG_FILE%"
echo Setup completed successfully: %DATE% %TIME% >> "%LOG_FILE%"

echo.
echo  ============================================================
echo  Setup complete!
echo  Next: Open Revit, go to the pyRevit tab, click Extensions,
echo  and enable KL^&A Tools. Then restart Revit or click Reload under the pyRevit tab.
echo  Log: %LOG_FILE%
echo  ============================================================
echo.
goto END

:FAILURE
echo Setup FAILED: %DATE% %TIME% >> "%LOG_FILE%"
echo.
echo  Setup did not complete. Send this log to your friendly pyRevit dev team members:
echo  %LOG_FILE%
echo.

:END
endlocal
pause