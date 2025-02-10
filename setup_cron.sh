#!/bin/bash

# Caminho para os scripts Python
SEND_ALL_CSVS_SCRIPT="/home/kali/staf-rasp/send_all_csvs.py"
SEND_CSV_SCRIPT="/home/kali/staf-rasp/send_csv.py"

# Verificar se o arquivo data_backup.csv existe e movê-lo para o diretório de backup
if [ -f "/home/kali/staf-rasp/data_backup.csv" ]; then
    mv /home/kali/staf-rasp/data_backup.csv /home/kali/staf-rasp/backup/
    echo "Arquivo data_backup.csv movido para o diretório de backup."
fi

# Adicionar tarefas ao crontab
(crontab -l 2>/dev/null; echo "0 * * * * /usr/bin/python3 $SEND_ALL_CSVS_SCRIPT") | crontab -
(crontab -l 2>/dev/null; echo "0 * * * * /usr/bin/python3 $SEND_CSV_SCRIPT") | crontab -

echo "Crontab configurado para executar os scripts a cada hora."
