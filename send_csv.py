import requests
from dotenv import load_dotenv
import os
import logging
import argparse
import shutil
import uuid

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configurar logging
log_file_path = os.path.expanduser('~/staf_rasp_send_csv.log')
handlers = [logging.FileHandler(log_file_path)]
if os.getenv('ENABLE_CONSOLE_LOGGING', 'false').lower() == 'true':
    handlers.append(logging.StreamHandler())  # Adiciona logging no terminal se habilitado

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=handlers
)

CSV_FILE_PATH = os.getenv('CSV_FILE_PATH')  # Caminho do arquivo CSV
ENDPOINT_URL = os.getenv('LARAVEL_STORE_ENDPOINT')  # URL do endpoint

def get_mac_address():
    # Obtém o endereço MAC do sistema
    try:
        mac = uuid.getnode()
        return mac_address
    except Exception as e:
        logging.error(f"Erro ao obter o MAC address: {e}")
        return None

def send_csv(file_path):
    if not os.path.exists(file_path):
        logging.error(f"CSV file {file_path} does not exist. Exiting.")
        return

    if os.stat(file_path).st_size == 0:
        logging.info(f"CSV file {file_path} is empty. Exiting.")
        return

    # Renomear o arquivo
    temp_file_path = file_path.replace('data_backup.csv', 'data_backup_temp.csv')
    shutil.move(file_path, temp_file_path)

    # Mover para a pasta temporária
    temp_dir = os.path.join(os.path.dirname(file_path), 'backup_temporario')
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = shutil.move(temp_file_path, os.path.join(temp_dir, os.path.basename(temp_file_path)))

    mac_address = get_mac_address()

    with open(temp_file_path, 'rb') as f:
        files = {'data_backup': f}
        data = {'mac_address': mac_address}
        try:
            response = requests.post(f"{ENDPOINT_URL}/api/raspberry-scan-store-offline", files=files, data=data)
            if response.status_code == 200:
                logging.info(f"CSV file {temp_file_path} sent successfully.")
                os.remove(temp_file_path)
                logging.info(f"CSV file {temp_file_path} deleted.")
            else:
                logging.error(f"Failed to send CSV file: {temp_file_path}, Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")

if __name__ == "__main__":
    logging.info("Scheduled execution of send_csv.py script.")
    parser = argparse.ArgumentParser(description="Send the entire CSV file to an endpoint.")
    parser.add_argument('--run', action='store_true', help="Run the CSV sending service")
    args = parser.parse_args()

    if args.run:
        logging.info("Starting the CSV sending service.")
        send_csv(CSV_FILE_PATH)
    else:
        logging.info("No action specified. Use --run to start the service.")
