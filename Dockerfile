FROM python:3.12-slim-bookworm

RUN useradd -ms /bin/bash appuser &&     apt-get update && apt-get install -y --no-install-recommends tini &&     rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
RUN mkdir -p /app/instance/uploads && chown -R appuser:appuser /app

USER appuser

ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=wsgi.py

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "wsgi:app"]
