FROM python:3.12-slim

RUN ["apt-get", "update"]

RUN ["pip", "install", "pipenv==2023.11.17"]

RUN ["mkdir", "/sandbox"]

# Copy Pipfile to the container
COPY Pipfile /sandbox/

# Set the working directory
WORKDIR /sandbox

# Install Python dependencies without creating a virtual environment
# First lock the Pipfile, then install
ENV PIPENV_VENV_IN_PROJECT=false
RUN pipenv lock && pipenv install --system --deploy


CMD ["sleep", "infinity"]