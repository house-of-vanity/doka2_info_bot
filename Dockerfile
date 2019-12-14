FROM python:3.7.4-stretch
WORKDIR /doka2_bot
COPY . /doka2_bot
RUN pip install -r requirements.txt
RUN python3 dota_news.py
CMD python3 /doka2_bot/app.py
