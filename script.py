import requests
import os
import uuid
import csv
from datetime import datetime
import time
import subprocess
import logging
from dotenv import load_dotenv
import tkinter as tk
from tkinter import scrolledtext, messagebox

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

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Raspberry Pi Manager")
        self.attributes("-fullscreen", True)  # Definir para tela cheia
        self.bind("<Escape>", self.exit_fullscreen)  # Tecla Esc para sair da tela cheia

        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.load_env()
        self.display_mac_address()
        self.display_IP_address()

    def create_widgets(self):
        # Entrada para código de barras
        self.label = tk.Label(self, text="Digite o código de barras:")
        self.label.pack(pady=10)

        self.barcode_entry = tk.Entry(self, width=50)
        self.barcode_entry.pack(pady=5)
        self.barcode_entry.bind("<Return>", self.process_barcode)

        self.submit_button = tk.Button(self, text="Enviar", command=self.process_barcode)
        self.submit_button.pack(pady=10)

        # Área de logs
        self.log_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=70, height=15)
        self.log_area.pack(pady=10)
        self.log_area.insert(tk.END, "Logs:\n")

        # Configuração do .env
        self.env_label = tk.Label(self, text="Configuração do arquivo .env:")
        self.env_label.pack(pady=10)

        self.env_text = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=70, height=10)
        self.env_text.pack(pady=5)

        self.save_button = tk.Button(self, text="Salvar .env", command=self.save_env)
        self.save_button.pack(pady=10)

    def display_mac_address(self):
        """Exibe o MAC Address no canto superior direito da janela."""
        mac_address = self.get_mac_address()
        if mac_address:
            self.mac_label = tk.Label(self, text=f"MAC Address: {mac_address}", font=("Arial", 10), fg="gray")
            # Posiciona no canto superior direito
    def display_IP_address(self):
            """Exibe o IP Address no canto superior direito da janela."""
            IP_address = self.get_public_ip()
            if IP_address:
                self.IP_label = tk.Label(self, text=f"IP Address: {IP_address}", font=("Arial", 10), fg="gray")
                # Posiciona no canto superior direito
    def exit_fullscreen(self, event=None):
        """Sair do modo de tela cheia ao pressionar Esc."""
        self.attributes("-fullscreen", False)

    def on_closing(self):
        if messagebox.askokcancel("Sair", "Tem certeza que deseja sair?"):
            self.destroy()
   

    def load_env(self):
        """Carrega o conteúdo do arquivo .env para a área de texto."""
        if os.path.exists('.env'):
            with open('.env', 'r') as env_file:
                content = env_file.read()
                self.env_text.insert(tk.END, content)

    def log(self, message):
        self.log_area.insert(tk.END, f"{message}\n")
        self.log_area.see(tk.END)

    def save_env(self):
        env_content = self.env_text.get("1.0", tk.END).strip()
        try:
            with open('.env', 'w') as env_file:
                env_file.write(env_content)
            messagebox.showinfo("Sucesso", "Arquivo .env salvo com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar o arquivo .env:\n{str(e)}")

    def process_barcode(self, event=None):
        barcode = self.barcode_entry.get().strip()
        if not barcode:
            messagebox.showwarning("Entrada Inválida", "Por favor, insira um código de barras.")
            return
        
        # Chama a função principal (ou a parte do código que precisa ser executada)
        self.run_main_process(barcode)
        self.barcode_entry.delete(0, tk.END)

    def run_main_process(self, barcode):
        try:
            mac_address = self.get_mac_address()
            public_ip = self.get_public_ip()
            
            if not mac_address or not public_ip:
                self.log("Não foi possível obter o MAC address ou IP público.")
                return
            
            validation_response = self.validate_raspberry(mac_address, public_ip, self.generate_ssh_key())
            if not validation_response:
                self.log("Falha na validação do Raspberry Pi.")
                return
            
            raspberry_id = validation_response.get('raspberry_id')
            filial_id = validation_response.get('filial_id')
            
            if not raspberry_id or not filial_id:
                self.log("IDs não encontrados na resposta da validação.")
                return
            
            self.store_ids(raspberry_id, filial_id)
            
            if not self.is_active(raspberry_id):
                self.log("Status inativo. O sistema não está operacional.")
                return
            
            self.insert_data(raspberry_id, barcode, filial_id)
        
        except Exception as e:
            self.log(f"Erro inesperado: {e}")

    def get_mac_address(self):
        try:
            mac = uuid.getnode()
            mac_address = ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))
            self.log(f"MAC Address: {mac_address}")
            return mac_address
        except Exception as e:
            self.log(f"Erro ao obter o MAC address: {e}")
            return None
    
    def get_public_ip(self):
        try:
            response = requests.get('https://api.ipify.org?format=json')
            response.raise_for_status()
            ip_data = response.json()
            return ip_data['ip']
        except requests.RequestException as e:
            self.log(f"Erro ao obter o IP público: {e}")
            return None
    
    def validate_raspberry(self, mac_address, public_ip, ssh_key_path):
        try:
            with open(ssh_key_path, 'r') as file:
                ssh_key = file.read().strip()
            response = requests.post(LARAVEL_VALIDATE_ENDPOINT, json={"mac_address": mac_address, "ip": public_ip, "ssh_key": ssh_key})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.log(f"Erro ao validar Raspberry Pi: {e}")
            return None

    def generate_ssh_key(self):
        ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")
        
        if not os.path.exists(ssh_key_path):
            self.log("Gerando chave SSH...")
            subprocess.run(["ssh-keygen", "-t", "rsa", "-b", "4096", "-f", ssh_key_path, "-N", ""])
        else:
            self.log("Chave SSH já existe.")
        
        return os.path.expanduser("~/.ssh/id_rsa.pub")

    def send_ssh_key(self, raspberry_id, ssh_key_path):
        try:
            with open(ssh_key_path, 'r') as file:
                ssh_key = file.read().strip()
            response = requests.post(LARAVEL_SSH_KEY_ENDPOINT, json={"raspberry_id": raspberry_id, "ssh_key": ssh_key})
            response.raise_for_status()
            self.log("Chave SSH enviada com sucesso.")
        except Exception as e:
            self.log(f"Erro ao enviar chave SSH: {e}")

    def store_ids(self, raspberry_id, filial_id):
        try:
            with open(IDS_FILE_PATH, 'w') as f:
                f.write(f"{raspberry_id}\n{filial_id}")
        except Exception as e:
            self.log(f"Erro ao armazenar IDs: {e}")

    def get_stored_ids(self):
        try:
            with open(IDS_FILE_PATH, 'r') as f:
                lines = f.readlines()
                return lines[0].strip(), lines[1].strip()
        except Exception as e:
            self.log(f"Erro ao ler IDs armazenados: {e}")
            return None, None

    def is_active(self, raspberry_id):
        try:
            response = requests.get(f"{LARAVEL_STATUS_ENDPOINT}/{raspberry_id}")
            response.raise_for_status()
            status = response.json().get('status', 'inativo')
            return status == 'ativo'
        except Exception as e:
            self.log(f"Erro ao verificar o status do Raspberry Pi: {e}")
            return False
    
    def insert_data(self, raspberry_id, codigobarras, filial_id):
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
                self.log("Dados enviados com sucesso")
            else:
                self.log(f"Erro ao enviar dados: {response.status_code}")
                self.backup_data_csv(raspberry_id, codigobarras, filial_id, data_time)
        except requests.exceptions.RequestException as e:
            self.log(f"Erro ao tentar conectar com o endpoint: {e}")
            self.backup_data_csv(raspberry_id, codigobarras, filial_id, data_time)

    def backup_data_csv(self, raspberry_id, codigobarras, filial_id, data_time):
        try:
            file_exists = os.path.isfile(CSV_FILE_PATH)
            with open(CSV_FILE_PATH, mode='a', newline='') as file:
                writer = csv.writer(file)
                if not file_exists:
                    writer.writerow(['timestamp', 'raspberry_id', 'codigobarras', 'filial_id'])
                writer.writerow([data_time, raspberry_id, codigobarras, filial_id])
            self.log("Dados salvos localmente no CSV")
        except Exception as e:
            self.log(f"Erro ao salvar dados no CSV: {e}")

    def on_closing(self):
        if messagebox.askokcancel("Sair", "Você realmente deseja sair?"):
            self.destroy()

if __name__ == "__main__":
    app = Application()
    app.mainloop()
