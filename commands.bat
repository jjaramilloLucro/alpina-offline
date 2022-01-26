ECHO OFF
docker stop dash_alpina
docker rm dash_alpina
docker rmi dash_alpina 
docker build -t dash_alpina .
docker run -dp 8081:80 --name dash_alpina dash_alpina
PAUSE