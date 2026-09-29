FROM python:3.12-slim
RUN pip install --no-cache-dir pandas==2.3.3
COPY test.sh /tests/test.sh
COPY grader.py /tests/grader.py
COPY inputs/ /app/inputs/
RUN chmod +x /tests/test.sh
WORKDIR /app
