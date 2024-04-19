FROM ubuntu:20.04

RUN apt update && apt install -y openssh-server
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

RUN useradd -m -s /bin/bash user
RUN echo "user:password" | chpasswd

ENTRYPOINT service ssh start && bash