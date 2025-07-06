
FROM python:3.11-slim


WORKDIR /app


COPY requirements.txt .


RUN pip install --upgrade pip && pip install -r requirements.txt


COPY . .


ENV PYTHONUNBUFFERED=1


EXPOSE 3000

CMD ["sh", "-c", "python wait-for-mysql.py && python src/main.py"]