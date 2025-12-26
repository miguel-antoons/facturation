#!/bin/bash
npm run build --prefix frontend/
docker build -t 192.168.1.155:5000/facturation_frontend:latest -f frontend/docker/Dockerfile .
docker build -t 192.168.1.155:5000/facturation_backend:latest -f backend/docker/Dockerfile .
docker build -t 192.168.1.155:5000/facturation_database:latest -f database/docker/Dockerfile .
docker push 192.168.1.155:5000/facturation_frontend:latest
docker push 192.168.1.155:5000/facturation_backend:latest
docker push 192.168.1.155:5000/facturation_database:latest
