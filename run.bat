@echo off
chcp 65001 >nul
echo Запуск веб-краулера...
echo.

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

python main.py

echo.
echo Нажмите любую клавишу для выхода...
pause >nul