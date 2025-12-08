@echo off
echo ===========================================
echo   CONSTRUYENDO EJECUTABLE OrdenaFotos
echo ===========================================
echo.
echo 1. Instalando dependencias...
pip install -r requirements.txt

echo.
echo 2. Limpiando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

echo.
echo 3. Generando ejecutable con PyInstaller...
echo    (Esto puede tardar unos minutos)
python -m PyInstaller --noconsole --onefile --name="OrdenaFotos_Pro" --clean ^
    --version-file="version_info.txt" ^
    --hidden-import=PIL ^
    --hidden-import=PIL._tkinter_finder ^
    --icon=NONE ^
    main_gui.py

if %errorlevel% neq 0 (
    echo.
    echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    echo   ERROR: Fallo al crear el ejecutable.
    echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo ===========================================
echo   PROCESO COMPLETADO
echo ===========================================
echo.
echo El ejecutable se encuentra en:
echo   %~dp0dist\OrdenaFotos_Pro.exe
echo.
pause
