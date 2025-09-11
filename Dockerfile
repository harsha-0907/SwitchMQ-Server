FROM python:3.11-slim

RUN apt-get update && apt-get install -y supervisor && rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt && \
    chmod +x devserver.sh
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
EXPOSE 42425 42426

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf", "-n"]