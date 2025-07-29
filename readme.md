python api_server.py -a src.app:app -p 8000 -w 2
streamlit run app.py


docker build -t trading-app-frontend -f docker/Dockerfile.frontend .
docker run --name frontend-container -d -p 8501:8501 trading-app-frontend

docker build -t trading-app-backend -f docker/Dockerfile.backend .
docker run --name backend-container -d -p 4000:8000 trading-app-backend "-a=server:app" "-w=2"

docker build -t realtime-data -f docker/Dockerfile.realtime_data .
docker run --name realtime-data-container -d realtime-data

docker build -t engine -f docker/Dockerfile.engine .
docker run --name engine-container -d engine