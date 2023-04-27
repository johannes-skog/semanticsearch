export PROJECT_NAME=external-ai

clear:

	echo ${PROJECT_NAME}

	docker-compose down

build:

	docker-compose build

up:

	docker-compose up -d

enter:

	docker exec -it ${PROJECT_NAME}  /bin/bash

