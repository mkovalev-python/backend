FROM python:3.7

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY ./entrypoint.sh .
RUN sed -i 's/\r//' ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

COPY . .

ENTRYPOINT ["sh","/usr/src/app/entrypoint.sh"]
