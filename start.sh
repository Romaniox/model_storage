# Start ssh server as root
nohup service ssh start &

# Continue as user MODEL_STORAGE_USERNAME to prevent problems with access rights 
echo ${MODEL_STORAGE_PASSWORD} | su ${MODEL_STORAGE_USERNAME}

# Create logging directory
mkdir /storage/logs/

# Start Fast API Server with additional API for model controlling
nohup uvicorn model_storage.app:app --host 0.0.0.0 --port 8300 &> /storage/logs/app.log &

# Start Triton Server in explicit mode
tritonserver --model-repository=/models --model-control-mode=explicit

# # Uncomment this and comment the line above in order to load all models when starting
# tritonserver --model-repository=/models --model-control-mode=explicit --load-model=*
