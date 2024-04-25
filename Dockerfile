# FROM ubuntu:20.04
# FROM nvcr.io/nvidia/tritonserver:23.08-py3
FROM server-modeler

RUN apt update && apt install -y openssh-server
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

RUN useradd -m -s /bin/bash user
RUN echo "user:password" | chpasswd

RUN pip install poetry==1.7.1
WORKDIR /app
COPY poetry.lock pyproject.toml /app/
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY model_storage/app.py /app/model_storage/app.py
COPY start.sh /app/

# ENTRYPOINT service ssh start
