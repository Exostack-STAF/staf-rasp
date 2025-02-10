import requests
from dotenv import load_dotenv
import os
import logging
import argparse
import shutil
import uuid
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

CSV_FILE_PATH = os.getenv('CSV_FILE_PATH')  # Caminho do arquivo CSV
ENDPOINT_URL = os.getenv('LARAVEL_STORE_ENDPOINT') + '/api/raspberry-scan-store-offline'  # URL do endpoint

# Caminho do arquivo de backup e pasta temporária
BACKUP_FILE_PATH = '/home/kali/staf-rasp/backup/data_backup.csv'
TEMP_DIR = '/home/kali/staf-rasp/backup_temporario'
TEMP_FILE_PATH = os.path.join(TEMP_DIR, 'data_backup_temp.csv')

# Caminho da pasta de backup permanente
PERMANENT_BACKUP_DIR = '/home/kali/staf-rasp/backup_permanente'

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
        
        session = requests.Session()
        retry = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        response = session.post(ENDPOINT_URL, files=files, data=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send file: {e}")
        response = None
    finally:
        for f in open_files:
            f.close()
    return response

def validate_and_cleanup(response):
    if response.status_code == 200:
        os.remove(TEMP_FILE_PATH)
    else:
        logging.error(f"Failed to send file: {response.status_code} - {response.text}")

def save_permanent_backup():
    if not os.path.exists(PERMANENT_BACKUP_DIR):
        os.makedirs(PERMANENT_BACKUP_DIR)
    timestamp = time.strftime("%Y%m%d%H%M%S")
    permanent_backup_file = os.path.join(PERMANENT_BACKUP_DIR, f'data_backup_{timestamp}.csv')
    shutil.copy(TEMP_FILE_PATH, permanent_backup_file)

def main():
    if rename_and_move_file():
        save_permanent_backup()
        response = send_file()
        validate_and_cleanup(response)
    else:
        logging.error("File renaming and moving failed. Exiting.")

if __name__ == "__main__":
    main()
