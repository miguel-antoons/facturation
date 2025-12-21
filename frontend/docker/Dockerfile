FROM nginx:latest

COPY frontend/docker/sites-enabled/facturation /etc/nginx/sites-enabled/facturation
COPY frontend/docker/nginx.conf /etc/nginx/nginx.conf
COPY frontend/dist /usr/share/nginx/html

EXPOSE 80