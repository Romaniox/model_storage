# FROM ubuntu:20.04
# FROM nvcr.io/nvidia/tritonserver:23.08-py3
FROM server-modeler

RUN apt update && apt install -y openssh-server
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

ARG USERNAME=user
ARG USER_UID=1000
ARG USER_GID=1000

RUN groupadd --gid $USER_GID $USERNAME && \
    useradd --uid $USER_UID --gid $USER_GID -m $USERNAME -s /bin/bash && \
    echo "$USERNAME ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

RUN echo "user:password" | chpasswd

RUN pip install poetry==1.7.1
WORKDIR /app
COPY poetry.lock pyproject.toml /app/
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY model_storage/app.py /app/model_storage/app.py
COPY start.sh /app/
RUN chown -R user:user /app
USER $USERNAME
