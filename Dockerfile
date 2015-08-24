FROM python:3.4

RUN [ "pip", "install", "aiohttp"]
RUN [ "pip", "install", "pytz"]

ADD ./remindmein /app/remindmein

WORKDIR "/app"

CMD [ "python", "remindmein/app.py" ]