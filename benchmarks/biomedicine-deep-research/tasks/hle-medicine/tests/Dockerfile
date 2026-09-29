FROM python:3.12-slim
COPY test.sh grade.py run_submission.py /tests/
COPY references/ /tests/references/
RUN chmod 700 /tests/references && chmod +x /tests/test.sh
WORKDIR /app
