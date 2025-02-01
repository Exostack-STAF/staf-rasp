import requests
from dotenv import load_dotenv
import os
import logging
import uuid

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

ENDPOINT_URL = os.getenv('LARAVEL_STORE_ENDPOINT') + '/api/raspberry-scan-store-offline'  # URL do endpoint
TEMP_DIR = '/home/kali/staf-rasp/backup_temporario'

def get_mac_address():
    try:
        mac = uuid.getnode()
        mac_address = ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))
        return mac_address
    except Exception as e:
        logging.error(f"Erro ao obter o MAC address: {e}")
        return None

def send_file(file_path):
    mac_address = get_mac_address()
    with open(file_path, 'rb') as f:
        files = {'data_backup': f}
        data = {'mac_address': mac_address}
        response = requests.post(ENDPOINT_URL, files=files, data=data)
    return response

def main():
    for filename in os.listdir(TEMP_DIR):
        file_path = os.path.join(TEMP_DIR, filename)
        if os.path.isfile(file_path):
            response = send_file(file_path)
            if response.status_code == 200:
                os.remove(file_path)
                logging.info(f"File {filename} sent and deleted successfully.")
            else:
                logging.error(f"Failed to send file {filename}: {response.status_code} - {response.text}")

if __name__ == "__main__":
    main()
