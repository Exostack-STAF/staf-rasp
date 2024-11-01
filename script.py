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
from pynput import keyboard

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações
LARAVEL_VALIDATE_ENDPOINT = os.getenv('LARAVEL_VALIDATE_ENDPOINT')
LARAVEL_STATUS_ENDPOINT = os.getenv('LARAVEL_STATUS_ENDPOINT')
LARAVEL_SSH_KEY_ENDPOINT = os.getenv('LARAVEL_SSH_KEY_ENDPOINT')
LARAVEL_STORE_ENDPOINT = os.getenv('LARAVEL_STORE_ENDPOINT')
RASPBERRY_ID = os.getenv('RASPBERRY_ID')
FILIAL_ID = os.getenv('FILIAL_ID')

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
        self.display_mac_address()

        # Iniciar listener de teclas
        self.listener = keyboard.Listener(on_press=self.on_key_press)
        self.listener.start()
    
    def create_widgets(self):
        # Entrada para código de barras
        self.label = tk.Label(self, text="Digite o código de barras:")
        self.label.pack(pady=10)

        self.log_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=150, height=40)
        self.log_area.pack(pady=10)
        self.log_area.insert(tk.END, "Logs:\n")

    def on_key_press(self, key):
        try:
            # Verifica se a tecla não é None
            if key is not None:  
                if hasattr(key, 'char') and key.char is not None:  # Para teclas normais
                    try:
                        self.barcode_entry += key.char  # Captura a tecla normal
                        self.log(f"Código Atual: {self.barcode_entry}")
                    except Exception as e:
                        self.log(f"Erro ao salvar a tecla: {e}")  # Mensagem de erro ao salvar a tecla
                elif key == keyboard.Key.enter:  # Se a tecla Enter for pressionada
                    self.process_barcode()
                    self.barcode_entry = ''  # Limpa o código acumulado após o processamento
        except AttributeError as e:
            self.log(f"Erro: {e}")  # Registra erro específico
            # Para teclas especiais
            self.log(f"Tecla especial pressionada: {key}")


     

    def display_mac_address(self):
        """Exibe o MAC Address no canto superior direito da janela."""
        mac_address = self.get_mac_address()
        if mac_address:
            self.mac_label = tk.Label(self, text=f"MAC Address: {mac_address}", font=("Arial", 30), fg="gray")
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
   
        self.log(f"Codigo: {barcode}")
   
        if not barcode:
            return
        self.barcode_entry.delete(0, tk.END)
        # Chama a função principal (ou a parte do código que precisa ser executada)
        self.insert_data(RASPBERRY_ID, barcode, FILIAL_ID)

    def get_mac_address(self):
        try:
            mac = uuid.getnode()
            mac_address = ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))
            self.log(f"MAC Address: {mac_address}")
            return mac_address
        except Exception as e:
            self.log(f"Erro ao obter o MAC address: {e}")
            return None
    
    def insert_data(self, raspberry_id, codigobarras, filial_id):
        try:
            data_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            payload = {
                'raspberry_id': RASPBERRY_ID,
                'codigo_barras': codigobarras,
                'data_time': data_time,
                'filial_id': FILIAL_ID
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
