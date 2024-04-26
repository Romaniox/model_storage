mkdir /storage/logs/

nohup service ssh start &
nohup uvicorn model_storage.app:app --host 0.0.0.0 --port 8300 &> /storage/logs/app.log &
tritonserver --model-repository=/models --model-control-mode=explicit #--load-model=*
