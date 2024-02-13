WORKDIR /app

COPY requirements.txt ./

RUN apk add build-base

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python","bot.py"]
