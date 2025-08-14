FROM python:3.12.10-slim-bullseye
LABEL authors="aleksander.marszalki"
LABEL name="cleanupy"

WORKDIR /src

RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    curl \
    software-properties-common \
    tzdata \
    cron \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get purge -y build-essential

RUN python -m pip install --upgrade pip --break-system-packages && \
    pip install uv --break-system-packages

COPY ./pyproject.toml ./uv.lock ./
RUN uv sync --no-cache --no-group dev

COPY ../src .

ENV PATH="/src/.venv/bin:/usr/local/bin:$PATH"

RUN mkdir /log

EXPOSE 8501/tcp

#CMD ["tail", "-f", "/dev/null"]

COPY docker/crontab /etc/cron.d/snapshooter-cron
RUN chmod 0644 /etc/cron.d/snapshooter-cron && \
    crontab /etc/cron.d/snapshooter-cron

#CMD ["streamlit", "run", "main.py", \
#     "--server.port", "8501", \
#     "--server.address", "0.0.0.0", \
#     "--server.enableCORS", "false", \
#     "--server.headless", "true"]

CMD bash -c "\
    cron -f & \
    streamlit run main.py \
        --server.port 8501 \
        --server.address 0.0.0.0 \
        --server.enableCORS false \
        --server.headless true \
"
