## Local
python server.py -a backend.app:app -p 8000 -w 2
streamlit run frontend.py

## Production
# Build with environment variable for Docker optimization
docker build -t cmv-pm-fe -f docker/Dockerfile.frontend .
docker run --name cmv-pm-fe-cont -d -p 8501:8501 --env-file .prod.env cmv-pm-fe

docker build -t cmv-pm-be -f docker/Dockerfile.backend .
docker run --name cmv-pm-be-cont -d -p 4000:8000 --env-file .prod.env cmv-pm-be "-a=server:app" "-w=2"

## Troubleshooting Docker Network Issues
# If Telegram API fails in Docker, try these commands:

# Test with custom DNS
docker run --name cmv-pm-be-cont -d -p 4000:8000 --dns 8.8.8.8 --dns 1.1.1.1 --env-file .prod.env cmv-pm-be "-a=server:app" "-w=2"

# Debug network connectivity inside container
docker exec -it cmv-pm-be-cont python test_docker_network.py

# Check container logs
docker logs cmv-pm-be-cont

# Restart container if needed
docker stop cmv-pm-be-cont && docker rm cmv-pm-be-cont