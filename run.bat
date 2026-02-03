@echo off
set ARG=%1

if "%ARG%"=="" (
    echo Starting FastAPI server == development
    uvicorn app.main:app --reload --reload-dir ./app --host 127.0.0.1 --port 8000
    @REM gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    goto :eof
)

if "%ARG%"=="mcp" (
    echo Starting FastAPI server == development
    uvicorn app.mcp_server.api:app --reload --reload-dir ./app --host 127.0.0.1 --port 8001
    @REM gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    goto :eof
)

if "%ARG%"=="legacy" (
    echo Starting FastAPI server == development
    uvicorn app.legacy_system.server:app --reload --reload-dir ./app --host 127.0.0.1 --port 7000
    @REM gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    goto :eof
)

if "%ARG%"=="mcp" (
    echo Starting FastAPI server == development
    uvicorn app.main:app --reload --reload-dir ./app --host 127.0.0.1 --port 8000
    @REM gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    goto :eof
)

if "%ARG%"=="graph" (
    @REM echo Starting FastAPI server == development
    python -m app.agent.graph    @REM gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    goto :eof
)