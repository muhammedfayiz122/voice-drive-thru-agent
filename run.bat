@echo off
set ARG=%1

if "%ARG%"=="" (
    echo Starting drive-thru agent 
    python -m app.main
    @REM gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    goto :eof
)

if "%ARG%"=="mcp" (
    echo Starting MCP server
    uvicorn app.mcp_server.api:app --reload --reload-dir ./app --host 127.0.0.1 --port 8001
    @REM gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    goto :eof
)

if "%ARG%"=="legacy" (
    echo Starting legacy system server
    uvicorn app.legacy_system.server:app --reload --reload-dir ./app --host 127.0.0.1 --port 7000
    @REM gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    goto :eof
)

if "%ARG%"=="kds" (
    echo Starting KDS server
    python -m app.kds.main 
    goto :eof
)

if "%ARG%"=="graph" (
    @REM echo Starting FastAPI server == development
    python -m app.agent.graph    @REM gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    goto :eof
)