FROM python:3.11-slim

RUN apt-get update && apt-get install -y supervisor && rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
EXPOSE 42425 42426
RUN pip install --no-cache-dir -r requirements.txt 

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
