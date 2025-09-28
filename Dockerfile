FROM python:3.11-slim
WORKDIR /app
COPY app_fastapi.py /app/
RUN pip install --no-cache-dir fastapi uvicorn
EXPOSE 8000
CMD ["uvicorn","app_fastapi:app","--host","0.0.0.0","--port","8000"]
