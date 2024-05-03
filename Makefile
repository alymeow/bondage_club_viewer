docker:
	docker build . -t bcv
	docker compose up -d

import:
	python3 import_json.py

run:
	python3 viewer.py
