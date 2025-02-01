#!/bin/bash

# Caminho para os scripts Python
SEND_ALL_CSVS_SCRIPT="/home/kali/staf-rasp/send_all_csvs.py"
SEND_CSV_SCRIPT="/home/kali/staf-rasp/send_csv.py"

# Adicionar tarefas ao crontab
(crontab -l 2>/dev/null; echo "0 0,6,12,18 * * * /usr/bin/python3 $SEND_ALL_CSVS_SCRIPT") | crontab -
(crontab -l 2>/dev/null; echo "0 0,6,12,18 * * * /usr/bin/python3 $SEND_CSV_SCRIPT") | crontab -

echo "Crontab configurado para executar os scripts às 00:00, 06:00, 12:00 e 18:00."
