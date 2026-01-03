#!/bin/bash
echo "Building frontend..."
npm run build --prefix frontend/
echo "Updating backend requirements..."
backend/venv/bin/python -m pip freeze > backend/requirements.txt
echo "Building docker images..."
docker build -t 192.168.1.155:5000/facturation_frontend:latest -f frontend/docker/Dockerfile .
docker build -t 192.168.1.155:5000/facturation_backend:latest -f backend/docker/Dockerfile .
docker build -t 192.168.1.155:5000/facturation_database:latest -f database/docker/Dockerfile .
if [ "$(git branch --show-current)" = "main" ]; then
    echo "On main branch, pushing docker images..."
    docker push 192.168.1.155:5000/facturation_frontend:latest
    docker push 192.168.1.155:5000/facturation_backend:latest
    docker push 192.168.1.155:5000/facturation_database:latest
else
    echo "Skipping docker push: Not on the main branch."
fi
