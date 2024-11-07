#!/bin/bash

echo "Criando o ambiente virtual..."
python3 -m venv /home/pi/staf-rasp/myenv

echo "Ativando o ambiente virtual..."
. /home/pi/staf-rasp/myenv/bin/activate

echo "Instalando as dependências..."
pip install -r /home/pi/staf-rasp/requeriment.txt

echo "Executando o script Python..."
python /home/pi/staf-rasp/script.py