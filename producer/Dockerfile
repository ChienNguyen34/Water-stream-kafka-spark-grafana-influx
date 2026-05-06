FROM python:3.11-slim

WORKDIR /app

# Cài thư viện trước (tận dụng Docker layer cache)
COPY producer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code producer
COPY producer/ ./producer/

# Copy dataset
COPY dataset/BATADAL_dataset03.csv ./dataset/
COPY dataset/BATADAL_dataset04.csv ./dataset/

# Chạy từ thư mục /app để import module đúng path
CMD ["python", "producer/producer.py"]
