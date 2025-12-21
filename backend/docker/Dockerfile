FROM python:3.13

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && pip install gunicorn
RUN apt update && apt upgrade -y && apt install -y default-jdk

COPY backend/app.py /app/app.py
COPY backend/ucanaccess-5.1.3-uber.jar /app/ucanaccess-5.1.3-uber.jar

COPY backend/controllers /app/controllers
COPY backend/database /app/database
COPY backend/models /app/models
COPY backend/pdf /app/pdf
COPY backend/routes /app/routes

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]