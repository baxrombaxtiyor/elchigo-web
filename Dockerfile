FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python3 manage.py collectstatic --noinput

EXPOSE 8000

CMD gunicorn elchigo.wsgi:application --bind 0.0.0.0:$PORT