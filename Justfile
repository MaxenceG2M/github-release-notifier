# https://github.com/casey/just

up: build
	docker compose up -d
	docker compose logs

build:
	docker compose build

rebuild: down
	docker compose build

down:
	docker compose down

force-build:
	docker compose build --no-cache
