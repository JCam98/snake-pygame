FROM python:3.10.8
RUN apt-get update
COPY . /app
WORKDIR /app
RUN pip install -r conf/requirements.txt
ENTRYPOINT ["bash", "scripts/run_snake.sh"]