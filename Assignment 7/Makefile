GATEWAY_DIR = gateway
APP_DIR     = ipo_explorer

.PHONY: start-gateway start-app stop

start-gateway:
	cd $(GATEWAY_DIR) && uv run main.py

start-app:
	cd $(APP_DIR) && .venv/bin/uvicorn server:app --port 8200 --reload

stop:
	-lsof -ti:8107 | xargs kill -9
	-lsof -ti:8200 | xargs kill -9
