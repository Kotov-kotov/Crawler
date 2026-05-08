@echo off
title Очистка путей Python
echo ========================================
echo ОЧИСТКА ПУТЕЙ PYTHON
echo ========================================
echo.

:: Удаляем старые пути из PATH (временное решение для текущей сессии)
setx PATH "%PATH:C:\Users\User\AppData\Local\Programs\Python\Python312\Scripts;=%" /M
setx PATH "%PATH:C:\Users\User\AppData\Local\Programs\Python\Python312;=%" /M

:: Обновляем переменные
refreshenv 2>nul

echo Старые пути удалены.
echo.

:: Проверка
where python

echo.
echo Если все еще видите Python312, удалите его вручную:
echo 1. Панель управления - Удаление программ
echo 2. Найти Python 3.12 и удалить
echo 3. Перезагрузить компьютер
echo.

pause