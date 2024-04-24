from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
import os
import zipfile
import shutil
import re  

app = FastAPI()

# Путь к репозиторию моделей Triton
MODEL_REPO_PATH = os.getenv('MODEL_REPOSITORY', '/models')


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
        
        version_match = re.search(r"versions: \[(\d+)\]", config_content)
        if version_match:
            return {"model_name": model_name, "version": version_match.group(1)}
        else:
            return JSONResponse(status_code=404, content={"message": "Version info not found in the config file"})
    except FileNotFoundError:
        return JSONResponse(status_code=404, content={"message": "Model config file not found"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6000)
