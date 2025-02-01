import requests
from dotenv import load_dotenv
import os
import logging
import argparse
import shutil
import uuid
import time

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

CSV_FILE_PATH = os.getenv('CSV_FILE_PATH')  # Caminho do arquivo CSV
ENDPOINT_URL = os.getenv('LARAVEL_STORE_ENDPOINT') + '/api/raspberry-scan-store-offline'  # URL do endpoint

# Caminho do arquivo de backup e pasta temporária
BACKUP_FILE_PATH = '/home/kali/staf-rasp/backup/data_backup.csv'
TEMP_DIR = '/home/kali/staf-rasp/backup_temporario'
TEMP_FILE_PATH = os.path.join(TEMP_DIR, 'data_backup_temp.csv')

def rename_and_move_file():
    global TEMP_FILE_PATH
    if not os.path.exists(BACKUP_FILE_PATH):
        logging.error(f"File not found: {BACKUP_FILE_PATH}")
        return False
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
    timestamp = time.strftime("%Y%m%d%H%M%S")
    temp_file_with_timestamp = os.path.join(TEMP_DIR, f'data_backup_temp_{timestamp}.csv')
    shutil.move(BACKUP_FILE_PATH, temp_file_with_timestamp)
    TEMP_FILE_PATH = temp_file_with_timestamp
    return True

def get_mac_address():
    try:
        mac = uuid.getnode()
        mac_address = ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))
        return mac_address
    except Exception as e:
        logging.error(f"Erro ao obter o MAC address: {e}")
        return None

def send_file():
    mac_address = get_mac_address()
    files = {}
    open_files = []
    try:
        for filename in os.listdir(TEMP_DIR):
            file_path = os.path.join(TEMP_DIR, filename)
            if os.path.isfile(file_path):
                f = open(file_path, 'rb')
                open_files.append(f)
                files['data_backup'] = f
        data = {'mac_address': mac_address}
        response = requests.post(ENDPOINT_URL, files=files, data=data)
    finally:
        for f in open_files:
            f.close()
    return response

def validate_and_cleanup(response):
    if response.status_code == 200:
        os.remove(TEMP_FILE_PATH)
    else:
        logging.error(f"Failed to send file: {response.status_code} - {response.text}")

def main():
    if rename_and_move_file():
        response = send_file()
        validate_and_cleanup(response)
    else:
        logging.error("File renaming and moving failed. Exiting.")

if __name__ == "__main__":
    main()
