#!/bin/bash

echo "Criando o ambiente virtual..."
python -m venv /home/pi/staf-rasp/myenv

echo "Ativando o ambiente virtual..."
source /home/pi/staf-rasp/myenv/bin/activate

echo "Instalando as dependências..."
pip install -r /home/pi/staf-rasp/requirements.txt

echo "Executando o script Python..."
python /home/pi/staf-rasp/script.py