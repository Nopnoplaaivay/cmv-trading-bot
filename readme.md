python server.py -a backend.app:app -p 8000 -w 2

docker build -t cmv-pm-fe -f docker/Dockerfile.frontend .
docker run --name cmv-pm-fe-cont -d -p 8501:8501 --env-file .prod.env cmv-pm-fe

docker build -t cmv-pm-be -f docker/Dockerfile.backend .
docker run --name cmv-pm-be-cont -d -p 4000:8000 --env-file .prod.env cmv-pm-be "-a=server:app" "-w=2"