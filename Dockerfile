FROM python:3.7-slim

WORKDIR /app

COPY requirements.txt /app
RUN pip install -r requirements.txt

COPY main.py /app

ENV MQTT_BROKER pluto
ENV DENON_HOST denon.fritz.box

CMD ["python", "main.py"]