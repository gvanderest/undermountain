FROM python:3
LABEL maintainer="Guillaume VanderEst <guillaume@vanderest.org>"

COPY . .
RUN pip install -r requirements.txt

EXPOSE 4200/TCP
EXPOSE 4201/TCP

VOLUME ["./data"]
CMD ["python", "um"]
