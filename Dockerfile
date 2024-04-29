FROM python:3.8

WORKDIR /app


RUN mkdir /data


COPY main.py ./
COPY utils.py ./
COPY comparison.py ./
COPY processing.py ./

COPY dataset.csv ./
COPY requirements.txt ./

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "./main.py"]

EXPOSE 8080
