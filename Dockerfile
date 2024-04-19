# FROM ubuntu:20.04
FROM nvcr.io/nvidia/tritonserver:23.08-py3

RUN apt update && apt install -y openssh-server
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

RUN useradd -m -s /bin/bash user
RUN echo "user:password" | chpasswd

WORKDIR /app
COPY start.sh /app/

# ENTRYPOINT service ssh start
