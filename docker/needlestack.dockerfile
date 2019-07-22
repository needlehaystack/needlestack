ARG BASE_IMAGE=${BASE_IMAGE:-3.7-slim-stretch}
FROM python:${BASE_IMAGE}

MAINTAINER Cung Tran "minishcung@gmail.com"

# Install BLAS for numpy and OpenMP for faiss
RUN apt update && \
        apt install -y libopenblas-dev libomp-dev make && \
        apt clean all

COPY . /app
WORKDIR /app

# A `MergerServicer` container doesn't not need all these requirements
RUN pip install -r /app/requirements-freeze.txt

RUN make compile-proto