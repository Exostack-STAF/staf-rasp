import requests
import os
import uuid
import csv
from datetime import datetime
import time
import threading
import logging
from dotenv import load_dotenv
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
from tkinter import font as tkfont
from pynput import keyboard
import socket

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações
LARAVEL_STORE_ENDPOINT = os.getenv('LARAVEL_STORE_ENDPOINT')
RASPBERRY_ID = os.getenv('RASPBERRY_ID')
FILIAL_ID = os.getenv('FILIAL_ID')

CSV_FILE_PATH = os.getenv('CSV_FILE_PATH')

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Raspberry Pi Manager")
        self.attributes("-fullscreen", True)  # Definir para tela cheia
        self.bind("<Escape>", self.exit_fullscreen)  # Tecla Esc para sair da tela cheia

        self.custom_font = tkfont.Font(family="Helvetica", size=12)
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.display_mac_address()

        self.internet_status_label = tk.Label(self, text="Verificando conexão...", font=self.custom_font, fg="gray")
        self.internet_status_label.pack(anchor='ne', padx=10, pady=10)
        self.check_internet_connection()

        # Iniciar listener de teclas
        self.listener = keyboard.Listener(on_press=self.on_key_press)
        self.listener.start()

        # Lista de códigos de barras não enviados
        self.failed_barcodes = []

    def create_widgets(self):
        # Notebook para abas
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both')

        # Aba principal
        self.main_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text='Principal')

        self.label = tk.Label(self.main_frame, text="Digite o código de barras:", font=self.custom_font)
        self.label.pack(pady=10)

        self.barcode_entry = tk.Entry(self.main_frame, width=50, state='disabled', font=self.custom_font)  # Cria um widget de entrada desabilitado
        self.barcode_entry.pack(pady=10)

        # Frame para logs lado a lado
        self.log_frame = ttk.Frame(self.main_frame)
        self.log_frame.pack(pady=10, fill='both', expand=True)

        self.log_area = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD, width=50, height=20, font=self.custom_font)
        self.log_area.pack(side='left', padx=5, pady=5, fill='both', expand=True)
        self.log_area.insert(tk.END, "Logs:\n")

        self.barcode_log_area = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD, width=50, height=20, font=self.custom_font)
        self.barcode_log_area.pack(side='right', padx=5, pady=5, fill='both', expand=True)
        self.barcode_log_area.insert(tk.END, "Códigos de Barras:\n")

        # Botão para sair do modo de tela cheia
        self.exit_fullscreen_button = tk.Button(self.main_frame, text="Sair do modo de tela cheia", command=self.exit_fullscreen, font=self.custom_font)
        self.exit_fullscreen_button.pack(pady=10)

        # Aba de configuração
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text='Configuração')

        self.env_text = scrolledtext.ScrolledText(self.config_frame, wrap=tk.WORD, width=150, height=40, font=self.custom_font)
        self.env_text.pack(pady=10)
        self.load_env()

        self.save_button = tk.Button(self.config_frame, text="Salvar .env", command=self.save_env, font=self.custom_font)
        self.save_button.pack(pady=10)

        # Aba de códigos não enviados
        self.failed_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.failed_frame, text='Códigos Não Enviados')

        self.failed_list = scrolledtext.ScrolledText(self.failed_frame, wrap=tk.WORD, width=150, height=40, font=self.custom_font)
        self.failed_list.pack(pady=10)
        self.failed_list.insert(tk.END, "Códigos de Barras Não Enviados:\n")

    def on_key_press(self, key):
        try:
            if key == keyboard.Key.enter:
                self.process_barcode()
            elif hasattr(key, 'char') and key.char is not None:
                self.barcode_entry.config(state='normal')
                self.barcode_entry.insert(tk.END, key.char)
                self.barcode_entry.config(state='disabled')
        except AttributeError as e:
            self.log(f"Erro: {e}")

    def display_mac_address(self):
        """Exibe o MAC Address, IP público, IP local e IP da rede local no canto superior direito da janela."""
        mac_address = self.get_mac_address()
        public_ip = self.get_public_ip()
        local_ip = self.get_local_ip()
        local_network_ip = self.get_local_network_ip()
        if mac_address and public_ip and local_ip and local_network_ip:
            self.mac_label = tk.Label(self, text=f"MAC: {mac_address}\nIP Público: {public_ip}\nIP Local: {local_ip}\nIP Rede Local: {local_network_ip}", font=self.custom_font, fg="gray")
            self.mac_label.pack(anchor='ne', padx=10, pady=10)  # Posiciona no canto superior direito

    def get_public_ip(self):
        try:
            response = requests.get('https://api.ipify.org?format=json')
            ip_address = response.json().get('ip')
            self.log(f"IP Público: {ip_address}")
            return ip_address
        except Exception as e:
            self.log(f"Erro ao obter o IP público: {e}")
            return None

    def get_local_ip(self):
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            self.log(f"IP Local: {local_ip}")
            return local_ip
        except Exception as e:
            self.log(f"Erro ao obter o IP local: {e}")
            return None

    def get_local_network_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0)
            s.connect(('192.168.1.1', 1))  # Pode ser qualquer IP na rede local
            local_network_ip = s.getsockname()[0]
            s.close()
            self.log(f"IP da Rede Local: {local_network_ip}")
            return local_network_ip
        except Exception as e:
            self.log(f"Erro ao obter o IP da rede local: {e}")
            return None

    def exit_fullscreen(self, event=None):
        """Sair do modo de tela cheia ao pressionar Esc ou clicar no botão."""
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
   
        self.barcode_log_area.insert(tk.END, f"Codigo: {barcode}\n")
        self.barcode_log_area.see(tk.END)
   
        if not barcode:
            return
        self.barcode_entry.config(state='normal')
        self.barcode_entry.delete(0, tk.END)
        self.barcode_entry.config(state='disabled')
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
        data_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        payload = {
            'raspberry_id': RASPBERRY_ID,
            'codigo_barras': codigobarras,
            'data_time': data_time,
            'filial_id': FILIAL_ID,
            'mac_address': self.get_mac_address()
        }

        def send_data():
            if not self.is_internet_available():
                self.log("Sem conexão com a internet. Salvando no CSV.")
                self.backup_data_csv(raspberry_id, codigobarras, filial_id, data_time)
                self.failed_barcodes.append(payload)
                self.update_failed_list()
                return

            try:
                response = requests.post(LARAVEL_STORE_ENDPOINT, json=payload)
                if response.status_code == 200:
                    success_message = response.json().get('message', 'Dados enviados com sucesso')
                    self.log(success_message)
                else:
                    self.log(f"Erro ao enviar dados: {response.status_code}")
                    self.backup_data_csv(raspberry_id, codigobarras, filial_id, data_time)
                    self.failed_barcodes.append(payload)
                    self.update_failed_list()
            except requests.exceptions.RequestException:
                self.log("Erro ao tentar conectar com o endpoint.")
                self.backup_data_csv(raspberry_id, codigobarras, filial_id, data_time)
                self.failed_barcodes.append(payload)
                self.update_failed_list()

        threading.Thread(target=send_data).start()

    def is_internet_available(self):
        try:
            requests.get('https://www.google.com', timeout=5)
            return True
        except requests.ConnectionError:
            return False

    def update_failed_list(self):
        self.failed_list.delete(1.0, tk.END)
        self.failed_list.insert(tk.END, "Códigos de Barras Não Enviados:\n")
        for payload in self.failed_barcodes:
            self.failed_list.insert(tk.END, f"{payload['codigo_barras']} - {payload['data_time']}\n")

    def backup_data_csv(self, raspberry_id, codigobarras, filial_id, data_time):
        try:
            file_exists = os.path.isfile(CSV_FILE_PATH)
            with open(CSV_FILE_PATH, mode='a', newline='') as file:
                writer = csv.writer(file)
                if not file_exists:
                    writer.writerow(['timestamp', 'raspberry_id', 'codigobarras', 'filial_id', 'mac_address'])
                writer.writerow([data_time, raspberry_id, codigobarras, filial_id, self.get_mac_address()])
            self.log("Dados salvos localmente no CSV")
        except Exception as e:
            self.log(f"Erro ao salvar dados no CSV: {e}")

    def check_internet_connection(self):
        def update_status():
            while True:
                try:
                    requests.get('https://www.google.com', timeout=5)
                    self.internet_status_label.config(text="Internet: Online", fg="green")
                except requests.ConnectionError:
                    self.internet_status_label.config(text="Internet: Offline", fg="red")
                time.sleep(10)

        threading.Thread(target=update_status, daemon=True).start()

    def retry_failed_barcodes(self):
        for payload in self.failed_barcodes:
            try:
                response = requests.post(LARAVEL_STORE_ENDPOINT, json=payload)
                if response.status_code == 200:
                    self.log(f"Retried successfully: {payload['codigo_barras']}")
                    self.failed_barcodes.remove(payload)
                else:
                    self.log(f"Retry failed: {payload['codigo_barras']}, Status code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                self.log(f"Retry error: {payload['codigo_barras']}, Error: {e}")

        self.update_failed_list()

if __name__ == "__main__":
    app = Application()
    app.after(60000, app.retry_failed_barcodes)  # Retry every 60 seconds
    app.mainloop()