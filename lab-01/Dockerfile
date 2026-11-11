FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /install/ /usr/local/
COPY --chown=2222:2222 app.py .

RUN mkdir -p /data && chown 2222:2222 /data
USER 2222:2222

EXPOSE 8080

CMD ["python", "app.py"]
