FROM python:3.10.8
COPY ./src /app
WORKDIR /app
RUN pip install -r requirements.txt
ENTRYPOINT ["bash", "run_snake.sh"]