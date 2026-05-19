FROM apache/spark:3.5.8-java17-python3

USER root

RUN pip install --no-cache-dir \
    "influxdb-client>=1.40.0" \
    "python-dotenv>=1.0.0" \
    "numpy>=1.23.0" \
    "pandas>=1.0.5" \
    "pyarrow>=4.0.0" \
    "scikit-learn==1.7.2"

USER spark
