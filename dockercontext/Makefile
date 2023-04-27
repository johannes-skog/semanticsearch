PROJECT_NAME=external-ai

WEIGHTS_PORT=8070

clear:

	docker stop ${PROJECT_NAME}
	docker rm ${PROJECT_NAME}
	docker rmi ${PROJECT_NAME}

build:

	docker stop ${PROJECT_NAME} || true && docker rm ${PROJECT_NAME} || true
	docker build -t ${PROJECT_NAME} .
	docker run -dt -w /workspace  --name ${PROJECT_NAME} -v ${PWD}/../:/workspace -w /workspace -p ${WEIGHTS_PORT}:${WEIGHTS_PORT} -p 8080:8080 -p 55069:55069 -p 55068:55068 -p 6006:6006 --env-file ../.env ${PROJECT_NAME} sleep infinity

enter:

	docker exec -it ${PROJECT_NAME}  /bin/bash

