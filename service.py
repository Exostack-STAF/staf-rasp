import csv
import requests
from dotenv import load_dotenv
import os
import logging
from datetime import datetime

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configurar logging
handlers = [logging.FileHandler('/var/log/staf_rasp_service.log')]
if os.getenv('ENABLE_CONSOLE_LOGGING', 'false').lower() == 'true':
    handlers.append(logging.StreamHandler())  # Adiciona logging no terminal se habilitado

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=handlers
)

CSV_FILE_PATH = os.getenv('CSV_FILE_PATH')  # Caminho do arquivo CSV
ENDPOINT_URL = os.getenv('LARAVEL_STORE_ENDPOINT')  # URL do endpoint

def update_last_sent_timestamp(timestamp):
    with open('/home/kali/staf-rasp/.env', 'a') as env_file:
        env_file.write(f'\nLAST_SENT_TIMESTAMP={timestamp}')
    logging.info(f"Updated LAST_SENT_TIMESTAMP in .env: {timestamp}")

def update_last_execution_timestamp():
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open('/home/kali/staf-rasp/.env', 'a') as env_file:
        env_file.write(f'\nLAST_EXECUTION_TIMESTAMP={timestamp}')
    logging.info(f"Updated LAST_EXECUTION_TIMESTAMP in .env: {timestamp}")

def read_csv_in_chunks(file_path, chunk_size=100):
    with open(file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        chunk = []
        for row in csv_reader:
            chunk.append(row)
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk

def read_csv_and_send_data():
    if not os.path.exists(CSV_FILE_PATH):
        logging.error(f"CSV file {CSV_FILE_PATH} does not exist. Exiting.")
        return

    if os.stat(CSV_FILE_PATH).st_size == 0:
        logging.info(f"CSV file {CSV_FILE_PATH} is empty. Exiting.")
        return

    all_data_sent = True

    for chunk in read_csv_in_chunks(CSV_FILE_PATH):
        for row in chunk:
            data = {
                'data_time': row['timestamp'],
                'raspberry_id': row['raspberry_id'],
                'codigo_barras': row['codigobarras'],
                'filial_id': row['filial_id'],
                'mac_address': row['mac_address'],
                'tipo': 'offline'
            }
            response = requests.post(f"{ENDPOINT_URL}/api/raspberry-scan-store-offline", json=data)
            if response.status_code == 200:
                logging.info(f"Data sent successfully: {data}")
                update_last_sent_timestamp(data['data_time'])
            else:
                logging.error(f"Failed to send data: {data}, Status code: {response.status_code}")
                all_data_sent = False

    if all_data_sent:
        os.remove(CSV_FILE_PATH)
        logging.info(f"CSV file {CSV_FILE_PATH} deleted.")
        update_last_execution_timestamp()
        logging.info("Service executed successfully.")
    else:
        logging.warning("Some data failed to send. CSV file not deleted.")

if __name__ == "__main__":
    read_csv_and_send_data()
