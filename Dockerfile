FROM python:3.6
MAINTAINER Guillaume VanderEst <guillaume@vanderest.org>

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 4200
EXPOSE 4201

VOLUME ["./data"]
ENTRYPOINT ["python", "um"]
