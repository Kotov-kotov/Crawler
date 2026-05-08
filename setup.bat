@echo off
chcp 65001 >nul
title Установка веб-краулера

echo ========================================
echo УСТАНОВКА ВЕБ-КРАУЛЕРА
echo ========================================
echo.

:: Проверка Python (без указания конкретного пути)
echo Проверка Python...
python --version 2>nul
if errorlevel 1 (
    echo [ОШИБКА] Python не найден в PATH
    echo.
    echo Пожалуйста, установите Python и отметьте "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo [OK] Python найден
python --version
echo.

:: Обновление pip
echo Обновление pip...
python -m pip install --upgrade pip
echo.

:: Установка библиотек
echo Установка библиотек...
python -m pip install requests
python -m pip install beautifulsoup4
python -m pip install pandas
python -m pip install networkx
python -m pip install plotly
python -m pip install urllib3
echo.

:: Создание папок
mkdir data 2>nul
mkdir graphs 2>nul

echo ========================================
echo УСТАНОВКА ЗАВЕРШЕНА
echo ========================================
echo.
echo Запустите run.bat
pause