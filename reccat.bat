@echo off
setlocal enabledelayedexpansion

REM Check if a parameter is provided. If not, default to the current folder.
if "%~1"=="" (
    set folderPath=%CD%
) else (
    set folderPath=%~1
)

REM Ensure the folder exists
if not exist "!folderPath!\" (
    echo The specified path does not exist or is not a directory.
    exit /b
)

REM Change the current directory to the provided folder
cd "!folderPath!"

REM Show tree structure of the current folder
echo Tree structure of the current folder:
tree

REM Recursively print the contents of .py, .js, .html, and .css files
for %%e in (py, js, html, css) do (
    for /r %%f in (*.%%e) do (
        REM Exclude files in the 'venv' directory
        echo "%%f" | findstr /C:"\venv\" >nul
        if errorlevel 1 (
            echo.
            echo Printing content of file: %%f
            type "%%f"
            echo.
            echo --- End of %%f ---
            echo.
        )
    )
)

endlocal
exit /b
