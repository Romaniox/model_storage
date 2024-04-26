import os
import zipfile
import shutil
import re  
import json
import httpx
from typing import Tuple
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse

# Путь к репозиторию моделей Triton
MODEL_REPO_PATH = os.getenv('MODEL_REPOSITORY', '/models')

# URL вашего Triton Server
TRITON_SERVER_URL = 'http://model_storage:8000'

app = FastAPI()


@app.post("/upload_model")
async def upload_model(file: UploadFile = File(...), model_name: str = Form(...), version: int = Form(None)):
    model_path = os.path.join(MODEL_REPO_PATH, model_name)
    model_version_path = os.path.join(model_path, str(version) if version else "1")

    os.makedirs(model_version_path, exist_ok=True)
    
    try:
        with zipfile.ZipFile(file.file, 'r') as zip_ref:
            zip_ref.extractall(model_version_path)
    except zipfile.BadZipFile:
        return JSONResponse(status_code=400, content={"message": "Invalid Zip file"})

    return {"message": f"Model '{model_name}' uploaded successfully with version {version or 1}"}


@app.post("/set_version/{model_name}")
async def set_version(model_name: str, version: int):
    model_path = os.path.join(MODEL_REPO_PATH, model_name)
    config_path = os.path.join(model_path, "config.pbtxt")
    
    try:
        with open(config_path, 'r') as file:
            lines = file.readlines()
        
        with open(config_path, 'w') as file:
            for line in lines:
                if line.startswith('version_policy: { specific: { versions: '):
                    file.write("version_policy: { specific: { versions: [" + str(version) + "]}}")
                else:
                    file.write(line)
    except FileNotFoundError:
        return JSONResponse(status_code=404, content={"message": "Model config file not found"})

    return {"message": f"Version set to {version} for model '{model_name}'"}


@app.get("/get_version/{model_name}")
async def get_version(model_name: str):
    config_path = os.path.join(MODEL_REPO_PATH, model_name, "config.pbtxt")
    
    try:
        with open(config_path, 'r') as file:
            config_content = file.read()
        
        version_match, version = _read_model_version(config_content)
        if not version_match:
            return JSONResponse(status_code=404, content={"message": "Version info not found in the config file"})
    except FileNotFoundError:
        return JSONResponse(status_code=404, content={"message": "Model config file not found"})
    return version

@app.get("/get_meta/{model_name}")
async def get_meta(model_name: str):
    config_path = os.path.join(MODEL_REPO_PATH, model_name, "config.pbtxt")
    try:
        with open(config_path, 'r') as file:
            config_content = file.read()

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Model config file not found")

    version_match, version = _read_model_version(config_content)
    if not version_match:
        raise HTTPException(status_code=404, detail="Version info not found in config file")
    
    meta_path = os.path.join(MODEL_REPO_PATH, model_name, version, "meta.json")
    
    try:
        with open(meta_path, 'r') as file:
            meta_data = json.load(file)
        return meta_data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Meta file not found")


@app.post("/load_model/{model_name}")
async def load_model(model_name: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{TRITON_SERVER_URL}/v2/repository/models/{model_name}/load")
        if response.status_code == 200:
            return {"message": f"Model '{model_name}' loaded successfully"}
        else:
            raise HTTPException(status_code=response.status_code, detail=response.json())

@app.post("/unload_model/{model_name}")
async def unload_model(model_name: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{TRITON_SERVER_URL}/v2/repository/models/{model_name}/unload")
        if response.status_code == 200:
            return {"message": f"Model '{model_name}' unloaded successfully"}
        else:
            raise HTTPException(status_code=response.status_code, detail=response.json())


@app.get("/index/")
async def index():
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{TRITON_SERVER_URL}/v2/repository/index")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json())
        
    return response.json()


@app.post("/upload_new_version/")
async def upload_new_version(src_file: UploadFile = File(...), model_name: str = Form(...), model_version: str = Form(...)):
    model_path = os.path.join(MODEL_REPO_PATH, model_name)
    
    # Проверяем все существующие версии модели в репозитории
    if find_triton_version(model_path, model_version) != -1:
        raise HTTPException(status_code=400, detail="This model version already exists.")
    
    # Путь для новой версии модели
    target_version_path = os.path.join(model_path, "1")  # Начнем с версии 1
    while os.path.exists(target_version_path):  # Увеличиваем номер версии, если папка уже существует
        version_number = int(os.path.basename(target_version_path)) + 1
        target_version_path = os.path.join(model_path, str(version_number))

    # Создаем директорию для новой версии
    os.makedirs(target_version_path, exist_ok=True)
    
    # Сохраняем и распаковываем архив
    temp_file_path = f"temp_{model_name}_{model_version}"
    
    #async with file as incoming_file
    with open(temp_file_path, 'wb') as temp_file:
        while data := await src_file.read(1024):  # Читаем файл по частям
            temp_file.write(data)
    
    with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
        zip_ref.extractall(target_version_path)

    os.remove(temp_file_path)

    # Чтение существующего meta.json и обновление
    meta_path = os.path.join(target_version_path, 'meta.json')
    if os.path.exists(meta_path):
        with open(meta_path, 'r') as file:
            meta_data = json.load(file)
    else:
        meta_data = {}
    
    # Обновление поля model_version
    meta_data['model_version'] = model_version
    with open(meta_path, 'w') as file:
        json.dump(meta_data, file)

    return {"version": model_version}


@app.post("/set_semantic_version/")
async def set_semantic_version(model_name: str, semantic_version: str):
    model_path = os.path.join(MODEL_REPO_PATH, model_name)

    # Проверяем каждую директорию в папке модели
    for version_dir in os.listdir(model_path):
        meta_path = os.path.join(model_path, version_dir, 'meta.json')
        if not os.path.exists(meta_path):
            continue
        
        with open(meta_path, 'r') as file:
            meta_data = json.load(file)
            
        if meta_data.get('model_version') != semantic_version:
            continue

        # Найдена версия, обновляем config.pbtxt
        config_path = os.path.join(model_path, 'config.pbtxt')
        if not os.path.exists(config_path):
            raise HTTPException(status_code=404, detail="Config file not found.")

        # Чтение и обновление config.pbtxt
        with open(config_path, 'r') as config_file:
            config_lines = config_file.readlines()

        with open(config_path, 'w') as config_file:
            for line in config_lines:
                if line.startswith("version_policy: { specific: { versions: ["):
                    config_file.write("version_policy: { specific: { versions: [" + str(version_dir) + "]}}")
                else:
                    config_file.write(line)

        return {"version": version_dir}

    raise HTTPException(status_code=404, detail="Semantic version not found.")


def find_triton_version(model_path: str, semantic_version: str):
    if not os.path.exists(model_path):
        return -1
    
    for version_dir in os.listdir(model_path):
        
        meta_path = os.path.join(model_path, version_dir, 'meta.json')
        if not os.path.exists(meta_path):
            continue

        with open(meta_path, 'r') as file:
            meta_data = json.load(file)
            if meta_data.get('model_version') == semantic_version:
                return version_dir
    
    return -1



def _read_model_version(config_content: str) -> Tuple[bool, str | None]:
    version_match = re.search(r"versions: \[(\d+)\]", config_content)
    if version_match:
        version = version_match.group(1)
        return True, version
    return False, None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6000)
