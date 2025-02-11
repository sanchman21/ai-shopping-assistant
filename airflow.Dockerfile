FROM apache/airflow:2.10.2

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    gcc \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


COPY airflow.requirements.txt requirements.txt

USER airflow

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt
