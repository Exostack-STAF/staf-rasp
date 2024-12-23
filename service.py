import csv
import requests
from dotenv import load_dotenv
import os
import logging
from datetime import datetime

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configurar logging
logging.basicConfig(filename='/var/log/staf_rasp_service.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CSV_FILE_PATH = os.getenv('CSV_FILE_PATH')  # Caminho do arquivo CSV
ENDPOINT_URL = os.getenv('LARAVEL_STORE_ENDPOINT')  # URL do endpoint

def handle_failed_request(data):
    with open(CSV_FILE_PATH, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([data['data_time'], data['raspberry_id'], data['codigo_barras'], data['filial_id'], data['mac_address']])
    logging.warning(f"Data saved locally for retry: {data}")

def update_last_sent_timestamp(timestamp):
    with open('/home/kali/staf-rasp/.env', 'a') as env_file:
        env_file.write(f'\nLAST_SENT_TIMESTAMP={timestamp}')
    logging.info(f"Updated LAST_SENT_TIMESTAMP in .env: {timestamp}")

def update_last_execution_timestamp():
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open('/home/kali/staf-rasp/.env', 'a') as env_file:
        env_file.write(f'\nLAST_EXECUTION_TIMESTAMP={timestamp}')
    logging.info(f"Updated LAST_EXECUTION_TIMESTAMP in .env: {timestamp}")

def read_csv_and_send_data():
    if os.stat(CSV_FILE_PATH).st_size == 0:
        logging.info(f"CSV file {CSV_FILE_PATH} is empty. Exiting.")
        return

    with open(CSV_FILE_PATH, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            data = {
                'data_time': row['timestamp'],
                'raspberry_id': row['raspberry_id'],
                'codigo_barras': row['codigobarras'],
                'filial_id': row['filial_id'],
                'mac_address': row['mac_address']
            }
            response = requests.post(ENDPOINT_URL, json=data)
            if response.status_code == 200:
                logging.info(f"Data sent successfully: {data}")
                update_last_sent_timestamp(data['data_time'])
            else:
                logging.error(f"Failed to send data: {data}, Status code: {response.status_code}")
                handle_failed_request(data)

    # Apagar o arquivo CSV após enviar os dados
    os.remove(CSV_FILE_PATH)
    logging.info(f"CSV file {CSV_FILE_PATH} deleted.")
    update_last_execution_timestamp()
    logging.info("Service executed successfully.")

if __name__ == "__main__":
    read_csv_and_send_data()
