FROM python:3.12-slim

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "flask", "--app", "app", "run","--host=0.0.0.0", "--port", "5000"]
