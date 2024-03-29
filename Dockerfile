FROM ubuntu:20.04

WORKDIR /app

ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && \
    apt-get install -y python3 \
                       python3-pip \
                       libgl1-mesa-glx \
                       libglib2.0-0

COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

RUN update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

COPY main.py processor.py detector.py ./
COPY cvbot ./cvbot
COPY data ./data

ENTRYPOINT ["python3", "main.py", "-c", "/options/config.json", "-l", "/logs"]
