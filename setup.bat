@echo off
chcp 65001 >nul
echo ========================================
echo УСТАНОВКА ВЕБ-КРАУЛЕРА
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    echo Скачайте Python с python.org
    pause
    exit /b 1
)

echo [OK] Python найден
python --version

echo.
echo Создание виртуального окружения...
if exist venv (
    echo Виртуальное окружение уже существует
) else (
    python -m venv venv
    echo [OK] Виртуальное окружение создано
)

echo.
echo Активация и установка зависимостей...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Создание папок...
mkdir data 2>nul
mkdir graphs 2>nul

echo.
echo ========================================
echo УСТАНОВКА ЗАВЕРШЕНА!
echo ========================================
echo.
echo Запустите проект: run.bat
echo.
pause