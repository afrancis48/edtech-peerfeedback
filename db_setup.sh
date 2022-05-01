#!/bin/bash

if [[ "$OSTYPE" == "msys" ]]; then
  winpty docker exec -it edtech-peerfeedback-web-1 flask db upgrade
  winpty docker exec -it edtech-peerfeedback-web-1 flask init-canvas --students 10 --tas 1
else
   docker exec -it edtech-peerfeedback-web-1 flask db upgrade
   docker exec -it edtech-peerfeedback-web-1 flask init-canvas --students 10 --tas 1
fi

cd frontend
yarn install
yarn serve