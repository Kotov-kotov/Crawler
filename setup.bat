@echo off
chcp 65001 >nul
title Установка веб-краулера

echo ========================================
echo УСТАНОВКА ВЕБ-КРАУЛЕРА
echo ========================================
echo.

:: Проверка Python
echo Проверка Python...
python --version 2>nul
if errorlevel 1 (
    echo [ОШИБКА] Python не найден
    pause
    exit /b 1
)
python --version
echo.

:: Обновление pip
echo Обновление pip...
python -m pip install --upgrade pip
echo.

:: Удаление старых версий
echo Удаление старых версий numpy и pandas...
python -m pip uninstall numpy pandas -y 2>nul
echo.

:: Установка совместимых версий
echo Установка numpy...
python -m pip install numpy==1.24.3

echo Установка pandas...
python -m pip install pandas==2.0.3

echo Установка остальных библиотек...
python -m pip install requests beautifulsoup4 networkx plotly urllib3
echo.

:: Проверка
echo Проверка установки...
python -c "import numpy; print('  numpy:', numpy.__version__)" 2>nul
python -c "import pandas; print('  pandas:', pandas.__version__)" 2>nul
python -c "import requests; print('  requests: OK')" 2>nul
echo.

:: Создание папок
mkdir data 2>nul
mkdir graphs 2>nul

echo ========================================
echo УСТАНОВКА ЗАВЕРШЕНА
echo ========================================
echo.
echo Запустите: run.bat
pause