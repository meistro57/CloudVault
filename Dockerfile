FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends rclone ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/cloudvault
COPY . .
RUN pip install --no-cache-dir .
ENTRYPOINT ["cloudvault"]
CMD ["status"]
