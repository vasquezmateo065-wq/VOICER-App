@echo off
REM ============================================================
REM  VOICER — Startup Script
REM  Inicia el backend FastAPI y el frontend Next.js en paralelo
REM ============================================================

echo.
echo  🎙️  Iniciando VOICER...
echo ============================================================
echo.

REM 1. Activar entorno virtual de Python
if exist "venv\Scripts\activate.bat" (
    echo [1/3] Activando entorno virtual Python...
    call venv\Scripts\activate.bat
) else (
    echo [!] No se encontro venv. Creando entorno virtual...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo [✓] Entorno virtual creado.
)

REM 2. Instalar dependencias del backend
echo [2/3] Verificando dependencias del backend...
pip install -r backend\requirements.txt --quiet
echo [✓] Dependencias listas.

REM 3. Iniciar backend y frontend
echo [3/3] Iniciando servidores...
echo.

REM Iniciar backend en una nueva ventana
start "VOICER Backend" cmd /k "cd /d %~dp0backend && call ..\venv\Scripts\activate.bat && echo 🖥️  Backend corriendo en http://localhost:8000 && echo. && uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"

REM Esperar un momento para que el backend arranque
timeout /t 3 /nobreak >nul

REM Iniciar frontend en otra ventana
if exist "frontend\node_modules" (
    start "VOICER Frontend" cmd /k "cd /d %~dp0frontend && echo 🎨 Frontend corriendo en http://localhost:3000 && echo. && npm run dev"
) else (
    echo [!] node_modules no encontrado en frontend. Instalando dependencias...
    cd frontend
    call npm install
    start "VOICER Frontend" cmd /k "cd /d %~dp0frontend && echo 🎨 Frontend corriendo en http://localhost:3000 && echo. && npm run dev"
    cd ..
)

echo.
echo ============================================================
echo  ✅ VOICER iniciado!
echo.
echo  🌐 Frontend: http://localhost:3000
echo  🖥️  Backend:  http://localhost:8000
echo  📖 API Docs: http://localhost:8000/docs
echo ============================================================
echo.
echo  💡 Pssst: Cerra las ventanas de los servidores para detenerlos.
echo.
pause
