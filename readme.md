## Local
python server.py -a backend.app:app -p 8000 -w 2
streamlit run frontend.py

## Production
# Build with environment variable for Docker optimization
docker build -t cmv-pm-fe -f docker/Dockerfile.frontend .
docker run --name cmv-pm-fe-cont -d -p 8011:8501 --env-file .prod.env cmv-pm-fe

docker build -t cmv-pm-be -f docker/Dockerfile.backend .
docker run --name cmv-pm-be-cont -d -p 8008:8000 --env-file .prod.env cmv-pm-be "-a=server:app" "-w=2"