# FROM nvcr.io/nvidia/tritonserver:23.08-py3
FROM server-modeler

RUN apt update && apt install -y openssh-server
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

ARG MODEL_STORAGE_USERNAME=user
ARG MODEL_STORAGE_PASSWORD=password
ARG MODEL_STORAGE_USER_UID=1000
ARG MODEL_STORAGE_USER_GID=1000

# ENV MODEL_STORAGE_USERNAME=user
# ENV MODEL_STORAGE_PASSWORD=password
# ENV MODEL_STORAGE_USER_UID=1000
# ENV MODEL_STORAGE_USER_GID=1000

RUN groupadd --gid $MODEL_STORAGE_USER_GID $MODEL_STORAGE_USERNAME && \
    useradd --uid $MODEL_STORAGE_USER_UID --gid $MODEL_STORAGE_USER_GID -m $MODEL_STORAGE_USERNAME -s /bin/bash && \
    echo "$MODEL_STORAGE_USERNAME ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

RUN echo "${MODEL_STORAGE_USERNAME}:${MODEL_STORAGE_PASSWORD}" | chpasswd

# # Создание группы, если она не существует
# RUN if ! getent group $MODEL_STORAGE_USER_GID; then groupadd --gid $MODEL_STORAGE_USER_GID $MODEL_STORAGE_USERNAME; fi

# # Создание пользователя, если он не существует
# RUN if ! id -u $MODEL_STORAGE_USER_UID > /dev/null 2>&1; then \
#       useradd --uid $MODEL_STORAGE_USER_UID --gid $MODEL_STORAGE_USER_GID -m $MODEL_STORAGE_USERNAME -s /bin/bash && \
#       echo "$MODEL_STORAGE_USERNAME ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers && \
#       echo "${MODEL_STORAGE_USERNAME}:${MODEL_STORAGE_PASSWORD}" | chpasswd; \
#     fi

RUN pip install poetry==1.7.1
WORKDIR /app
COPY poetry.lock pyproject.toml /app/
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY model_storage/app.py /app/model_storage/app.py
COPY start.sh /app/
RUN chown -R $MODEL_STORAGE_USERNAME:$MODEL_STORAGE_USERNAME /app
# USER $MODEL_STORAGE_USERNAME
