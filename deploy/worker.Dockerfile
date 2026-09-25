FROM python:3.12-slim

WORKDIR /srv
COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY worker/exporter ./exporter

ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "exporter.main"]
