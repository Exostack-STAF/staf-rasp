import csv
import requests
import time
from datetime import datetime
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

CSV_FILE_PATH = os.getenv('CSV_FILE_PATH')  # Caminho do arquivo CSV
ENDPOINT_URL = os.getenv('LARAVEL_STORE_ENDPOINT')  # URL do endpoint

def handle_failed_request(data):
    with open(CSV_FILE_PATH, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([data['data_time'], data['raspberry_id'], data['codigo_barras'], data['filial_id'], data['mac_address']])
    print(f"Data saved locally for retry: {data}")

def read_csv_and_send_data():
    with open(CSV_FILE_PATH, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            data = {
                'data_time': row['timestamp'],
                'raspberry_id': row['raspberry_id'],
                'codigo_barras': row['codigobarras'],
                'filial_id': row['filial_id'],
               
            }
            response = requests.post(ENDPOINT_URL, json=data)
            if response.status_code == 200:
                print(f"Data sent successfully: {data}")
            else:
                print(f"Failed to send data: {data}, Status code: {response.status_code}")
                handle_failed_request(data)

    # Apagar o arquivo CSV após enviar os dados
    os.remove(CSV_FILE_PATH)
    print(f"CSV file {CSV_FILE_PATH} deleted.")

if __name__ == "__main__":
    read_csv_and_send_data()
