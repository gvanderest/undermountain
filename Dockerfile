FROM python:3.6
LABEL maintainer="Guillaume VanderEst <guillaume@vanderest.org>"

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 4200/TCP
EXPOSE 4201/TCP

VOLUME ["./data"]
CMD ["python", "um"]
