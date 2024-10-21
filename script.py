import requests
import os
import uuid
import csv
from datetime import datetime
import time
import subprocess
import logging
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações
LARAVEL_VALIDATE_ENDPOINT = os.getenv('LARAVEL_VALIDATE_ENDPOINT')
LARAVEL_STATUS_ENDPOINT = os.getenv('LARAVEL_STATUS_ENDPOINT')
LARAVEL_SSH_KEY_ENDPOINT = os.getenv('LARAVEL_SSH_KEY_ENDPOINT')
LARAVEL_STORE_ENDPOINT = os.getenv('LARAVEL_STORE_ENDPOINT')

MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST'),
    'database': os.getenv('MYSQL_DATABASE'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD')
}
IDS_FILE_PATH = os.getenv('IDS_FILE_PATH')
CSV_FILE_PATH = os.getenv('CSV_FILE_PATH')

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_mac_address():
    try:
        mac = uuid.getnode()
        mac_address = ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))
        logging.info(f"MAC Address: {mac_address}")
        return mac_address
    except Exception as e:
        logging.error("Erro ao obter o MAC address: %s", e)
        return None
    
def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        response.raise_for_status()
        ip_data = response.json()
        return ip_data['ip']
    except requests.RequestException as e:
        logging.error(f"Erro ao obter o IP público: {e}")
        return None
    
def validate_raspberry(mac_address, public_ip, ssh_key_path):
    try:
        with open(ssh_key_path, 'r') as file:
            ssh_key = file.read().strip()
        response = requests.post(LARAVEL_VALIDATE_ENDPOINT, json={"mac_address": mac_address, "ip": public_ip, "ssh_key": ssh_key})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error("Erro ao validar Raspberry Pi: %s", e)
        return None

def generate_ssh_key():
    ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")
    
    if not os.path.exists(ssh_key_path):
        logging.info("Gerando chave SSH...")
        subprocess.run(["ssh-keygen", "-t", "rsa", "-b", "4096", "-f", ssh_key_path, "-N", ""])
    else:
        logging.info("Chave SSH já existe.")
    
    return os.path.expanduser("~/.ssh/id_rsa.pub")

def send_ssh_key(raspberry_id, ssh_key_path):
    try:
        with open(ssh_key_path, 'r') as file:
            ssh_key = file.read().strip()
        response = requests.post(LARAVEL_SSH_KEY_ENDPOINT, json={"raspberry_id": raspberry_id, "ssh_key": ssh_key})
        response.raise_for_status()
        logging.info("Chave SSH enviada com sucesso.")
    except Exception as e:
        logging.error("Erro ao enviar chave SSH: %s", e)

def store_ids(raspberry_id, filial_id):
    try:
        with open(IDS_FILE_PATH, 'w') as f:
            f.write(f"{raspberry_id}\n{filial_id}")
    except Exception as e:
        logging.error("Erro ao armazenar IDs: %s", e)

def get_stored_ids():
    try:
        with open(IDS_FILE_PATH, 'r') as f:
            lines = f.readlines()
            return lines[0].strip(), lines[1].strip()
    except Exception as e:
        logging.error("Erro ao ler IDs armazenados: %s", e)
        return None, None

def is_active(raspberry_id):
    try:
        response = requests.get(f"{LARAVEL_STATUS_ENDPOINT}/{raspberry_id}")
        response.raise_for_status()
        status = response.json().get('status', 'inativo')
        return status == 'ativo'
    except Exception as e:
        logging.error("Erro ao verificar o status do Raspberry Pi: %s", e)
        return False
    
def insert_data( raspberry_id, codigobarras, filial_id):
    try:
        data_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        payload = {
            'raspberry_id': raspberry_id,
            'codigo_barras': codigobarras,
            'data_time': data_time,
            'filial_id': filial_id
        }
        
        response = requests.post(LARAVEL_STORE_ENDPOINT, json=payload)
        
        if response.status_code == 200:
            logging.info("Dados enviados com sucesso")
        else:
            logging.error("Erro ao enviar dados: %s", response.status_code)
            backup_data_csv(raspberry_id, codigobarras, filial_id, data_time)
    except requests.exceptions.RequestException as e:
        logging.error("Erro ao tentar conectar com o endpoint: %s", e)
        backup_data_csv(raspberry_id, codigobarras, filial_id, data_time)

def backup_data_csv(raspberry_id, codigobarras, filial_id, data_time):
    try:
        file_exists = os.path.isfile(CSV_FILE_PATH)
        with open(CSV_FILE_PATH, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['timestamp', 'raspberry_id', 'codigobarras', 'filial_id'])
            writer.writerow([data_time, raspberry_id, codigobarras, filial_id])
        logging.info("Dados salvos localmente no CSV")
    except Exception as e:
        logging.error("Erro ao salvar dados no CSV: %s", e)

def read_barcode():
    try:
        barcode = input("Digite o código de barras: ").strip()
        return barcode
    except Exception as e:
        logging.error("Erro ao ler o código de barras: %s", e)
        return None

def open_fullscreen_terminal():
    import os
    import sys
    
    if sys.platform == "win32":
        os.system("mode con: cols=9999 lines=9999")  # Ajusta a janela do console no Windows
    elif sys.platform == "darwin":  # macOS
        os.system("osascript -e 'tell application \"Terminal\" to set bounds of front window to {0, 0, 1920, 1080}'")  # Ajuste o tamanho conforme necessário
    elif sys.platform == "linux":  # Linux
        os.system("printf '\033[8;1000;1920t'")  # Ajuste o tamanho conforme necessário



def main():
    open_fullscreen_terminal()
    while True:
        try:
            mac_address = get_mac_address()
            public_ip = get_public_ip()
            
            if not mac_address or not public_ip:
                logging.error("Não foi possível obter o MAC address ou IP público")
                time.sleep(5)  # Aguarda um tempo antes de tentar novamente
                continue
            
            validation_response = validate_raspberry(mac_address, public_ip, generate_ssh_key())
            if not validation_response:
                logging.error("Falha na validação do Raspberry Pi")
                time.sleep(5)  # Aguarda um tempo antes de tentar novamente
                continue
            
            raspberry_id = validation_response.get('raspberry_id')
            filial_id = validation_response.get('filial_id')
            
            if not raspberry_id or not filial_id:
                logging.error("IDs não encontrados na resposta da validação")
                time.sleep(5)  # Aguarda um tempo antes de tentar novamente
                continue
            
            store_ids(raspberry_id, filial_id)
            
            if not is_active(raspberry_id):
                logging.warning("Status inativo. O sistema não está operacional.")
                time.sleep(5)  # Aguarda um tempo antes de tentar novamente
                continue
            
            barcode = read_barcode()
            if barcode:
                insert_data(raspberry_id, barcode, filial_id)
            else:
                logging.warning("Nenhum código de barras encontrado.")
            
            time.sleep(0.5)  # Ajuste o tempo de espera conforme necessário
        
        except Exception as e:
            logging.error(f"Erro inesperado: {e}")
            time.sleep(10)  # Aguarda um tempo mais longo em caso de erro inesperado

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)  # Configura o nível de logging
    main()