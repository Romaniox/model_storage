# Model Storage

Этот репозиторий является хранилищем данных, 
использующего Triton Server для хостинга моделей машинного обучения, 
FastAPI для обеспечения REST API для работы с этими моделями 
и SSH сервер для удаленного доступа к данным.

## Особенности

- **SSH доступ**: Удаленный доступ к файлам и данным внутри контейнера.
- **Triton Inference Server**: Эффективное выполнение моделей машинного обучения из хранилища.
- **FastAPI**: веб-фреймворк для создания API для работы с репозиторием моделей от Triton Server

## Требования

- Docker
- Docker Compose

## Установка и запуск

### Клонирование репозитория

```bash
git clone https://github.com/SanchoPanso/model_storage.git
cd model_storage
```

### Запуск

```bash
docker-compose up --build -d
```

### Открывающиеся порты 

- 4000 - SSH
- 8100-8103 - Triton Server
- 8300 - Fast API

