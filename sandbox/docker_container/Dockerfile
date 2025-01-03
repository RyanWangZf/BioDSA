FROM rocker/r-ver

RUN ["apt-get", "update"]

# Support R execution:
# Install system dependencies for R packages.
RUN ["apt-get", "install", "-y", "libxml2-dev"]
RUN ["apt-get", "install", "-y", "libpng-dev"]
RUN ["apt-get", "install", "-y", "libcurl4-openssl-dev"]
RUN ["apt-get", "install", "-y", "libfontconfig1-dev"]
RUN ["apt-get", "install", "-y", "libssl-dev"]

# Install system dependencies
RUN ["apt-get", "install", "-y", "cmake"]

COPY install_packages.r /tmp/install_libraries.r

RUN ["Rscript", "/tmp/install_libraries.r"]


# Support Python execution:
# Install Python 3.10 and pip
RUN ["apt-get", "install", "-y", "python3.10", "python3-pip"]

# Set Python 3.10 as the default Python version
RUN ["update-alternatives", "--install", "/usr/bin/python", "python", "/usr/bin/python3.10", "1"]

# Install pipenv
RUN ["pip", "install", "pipenv==2023.11.17"]

RUN ["mkdir", "/sandbox"]

# Copy Pipfile and Pipfile.lock to the container
COPY Pipfile /sandbox
COPY Pipfile.lock /sandbox

# Set the working directory
WORKDIR /sandbox

# Install Python dependencies from Pipfile.lock without creating a virtual environment
ENV PIPENV_VENV_IN_PROJECT=false
RUN ["pipenv", "install", "--system", "--deploy"]


CMD ["sleep", "infinity"]