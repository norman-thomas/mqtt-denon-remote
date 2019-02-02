FROM python:3.7-slim

RUN pip install --upgrade pip

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

ENV MQTT_BROKER pluto
ENV DENON_HOST denon.fritz.box

CMD ["python", "main.py"]
