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

def _read_model_version(config_content: str) -> Tuple[bool, str | None]:
    version_match = re.search(r"versions: \[(\d+)\]", config_content)
    if version_match:
        version = version_match.group(1)
        return True, version
    return False, None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6000)
