import requests
from dotenv import load_dotenv
import os
import logging
import argparse
import shutil
import uuid

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

CSV_FILE_PATH = os.getenv('CSV_FILE_PATH')  # Caminho do arquivo CSV
ENDPOINT_URL = os.getenv('LARAVEL_STORE_ENDPOINT') + '/api/raspberry-scan-store-offline'  # URL do endpoint

# Caminho do arquivo de backup e pasta temporária
BACKUP_FILE_PATH = '/backup/data_backup.csv'
TEMP_DIR = 'backup_temporario'
TEMP_FILE_PATH = os.path.join(TEMP_DIR, 'data_backup_temp.csv')

def rename_and_move_file():
    if not os.path.exists(BACKUP_FILE_PATH):
        logging.error(f"File not found: {BACKUP_FILE_PATH}")
        return False
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
    shutil.move(BACKUP_FILE_PATH, TEMP_FILE_PATH)
    return True

def send_file():
    with open(TEMP_FILE_PATH, 'rb') as f:
        response = requests.post(ENDPOINT_URL, files={'file': f})
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
