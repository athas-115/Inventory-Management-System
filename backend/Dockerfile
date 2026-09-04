FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt ./backend-requirements.txt
COPY ai_agent/requirements.txt ./ai-agent-requirements.txt
COPY mcp_server/requirements.txt ./mcp-requirements.txt

RUN pip install --no-cache-dir \
    -r backend-requirements.txt \
    -r ai-agent-requirements.txt \
    -r mcp-requirements.txt

COPY backend/app ./app
COPY ai_agent ./ai_agent
COPY mcp_server ./mcp_server

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]