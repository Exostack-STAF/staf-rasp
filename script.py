import requests
import os
import uuid
import csv
from datetime import datetime, timedelta
import time
import threading
import logging
from dotenv import load_dotenv
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
from tkinter import font as tkfont
from pynput import keyboard
import socket
import subprocess

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
        
        self.last_sent_timestamp = tk.StringVar()
        self.last_service_send_timestamp = tk.StringVar()
        self.update_last_service_send_timestamp()
        self.last_sent_timestamp.set(f"Último envio dos códigos de barras em modo offline: {self.get_last_sent_timestamp()}")
        
        self.current_timestamp = tk.StringVar()
        self.update_current_timestamp()
        
        try:
            self.logo_image = tk.PhotoImage(file="logo.png").subsample(10, 10)  # Resize the logo to be smaller
        except tk.TclError:
            self.logo_image = None
            logging.error("Logo image not found. Continuing without logo.")
        
        self.laravel_store_endpoint = tk.StringVar(value=f"Servidor: {LARAVEL_STORE_ENDPOINT}")
        self.barcode_status = tk.StringVar(value="Status: Aguardando...")
        self.create_widgets()
        self.load_backup_csv()  # Load CSV content on startup
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.display_mac_address()

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
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky='w')

        self.barcode_entry = tk.Entry(self.main_frame, width=50, state='disabled', font=self.custom_font)  # Cria um widget de entrada desabilitado
        self.barcode_entry.grid(row=0, column=1, padx=10, pady=10, sticky='w')

        if self.logo_image:
            self.logo_label = tk.Label(self.main_frame, image=self.logo_image)
            self.logo_label.grid(row=0, column=2, padx=10, pady=10, sticky='w')

        # Frame para logs
        self.log_frame = ttk.Frame(self.main_frame)
        self.log_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky='nsew')

        self.log_area_label = tk.Label(self.log_frame, text="Log de Batimentos", font=self.custom_font)
        self.log_area_label.pack(anchor='nw', padx=5, pady=5)
        self.log_area = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD, width=50, height=10, font=self.custom_font)
        self.log_area.pack(side='left', padx=5, pady=5, fill='both', expand=True)

        self.barcode_log_area_response_label = tk.Label(self.log_frame, text="Resposta do Endpoint", font=self.custom_font)
        self.barcode_log_area_response_label.pack(anchor='ne', padx=5, pady=5)
        self.barcode_log_area_response = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD, width=50, height=10, font=self.custom_font)
        self.barcode_log_area_response.pack(side='right', padx=5, pady=5, fill='both', expand=True)

        # Frame para logs de sucesso e falha
        self.success_log_frame = ttk.Frame(self.main_frame)
        self.success_log_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky='nsew')

        self.success_log_area_label = tk.Label(self.success_log_frame, text="Log de Sucesso", font=self.custom_font, fg="green")
        self.success_log_area_label.pack(anchor='nw', padx=5, pady=5)
        self.success_log_area = scrolledtext.ScrolledText(self.success_log_frame, wrap=tk.WORD, width=50, height=10, font=self.custom_font, fg="green")
        self.success_log_area.pack(side='left', padx=5, pady=5, fill='both', expand=True)

        self.failed_log_area_label = tk.Label(self.success_log_frame, text="Log de Falha", font=self.custom_font, fg="red")
        self.failed_log_area_label.pack(anchor='ne', padx=5, pady=5)
        self.failed_log_area = scrolledtext.ScrolledText(self.success_log_frame, wrap=tk.WORD, width=50, height=10, font=self.custom_font, fg="red")
        self.failed_log_area.pack(side='right', padx=5, pady=5, fill='both', expand=True)

        # Frame para informações de rede
        self.network_info_frame = ttk.Frame(self.main_frame)
        self.network_info_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky='nsew')

        self.network_info_label = tk.Label(self.network_info_frame, text="", font=self.custom_font, fg="gray")
        self.network_info_label.pack(anchor='ne', padx=10, pady=10)

        # Indicator for system online status
        self.internet_status_label = tk.Label(self.network_info_frame, text="Internet: Offline", font=self.custom_font, fg="red")
        self.internet_status_label.pack(anchor='ne', padx=10, pady=10)

        self.current_timestamp_label = tk.Label(self.network_info_frame, textvariable=self.current_timestamp, font=self.custom_font, fg="yellow")
        self.current_timestamp_label.pack(anchor='ne', padx=10, pady=10)

        self.last_sent_label = tk.Label(self.network_info_frame, textvariable=self.last_sent_timestamp, font=self.custom_font, fg="gray")
        self.last_sent_label.pack(anchor='ne', padx=10, pady=10)

        # Label para exibir o LARAVEL_STORE_ENDPOINT
        self.laravel_store_endpoint_label = tk.Label(self.network_info_frame, textvariable=self.laravel_store_endpoint, font=self.custom_font, fg="green")
        self.laravel_store_endpoint_label.pack(anchor='ne', padx=10, pady=10)

        # Label para exibir o status do envio do código de barras
        self.barcode_status_label = tk.Label(self.network_info_frame, textvariable=self.barcode_status, font=self.custom_font, fg="orange")
        self.barcode_status_label.pack(anchor='ne', padx=10, pady=10)

        # Botão para sair do modo de tela cheia
        self.exit_fullscreen_button = tk.Button(self.main_frame, text="Sair do modo de tela cheia", command=self.exit_fullscreen, font=self.custom_font)
        self.exit_fullscreen_button.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky='w')

        # Botões para enviar CSVs
        self.send_csv_button = tk.Button(self.main_frame, text="Enviar CSV", command=self.send_csv, font=self.custom_font)
        self.send_csv_button.grid(row=5, column=0, padx=10, pady=10, sticky='w')

        self.send_all_csvs_button = tk.Button(self.main_frame, text="Enviar Todos CSVs", command=self.send_all_csvs, font=self.custom_font)
        self.send_all_csvs_button.grid(row=5, column=1, padx=10, pady=10, sticky='w')

        # Botão para carregar CSV de backup
        self.load_backup_csv_button = tk.Button(self.main_frame, text="Carregar CSV de Backup", command=self.load_backup_csv, font=self.custom_font)
        self.load_backup_csv_button.grid(row=5, column=2, padx=10, pady=10, sticky='w')

        # Aba de configuração
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text='Configuração')

        self.config_label = tk.Label(self.config_frame, text="Configurações do .env", font=self.custom_font)
        self.config_label.grid(row=0, column=0, padx=10, pady=10, sticky='w')

        self.laravel_endpoint_label = tk.Label(self.config_frame, text="URL do Sistema:", font=self.custom_font)
        self.laravel_endpoint_label.grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.laravel_endpoint_entry = tk.Entry(self.config_frame, width=50, font=self.custom_font)
        self.laravel_endpoint_entry.grid(row=1, column=1, padx=10, pady=10, sticky='w')
        if LARAVEL_STORE_ENDPOINT:
            self.laravel_endpoint_entry.insert(0, LARAVEL_STORE_ENDPOINT)

        self.raspberry_id_label = tk.Label(self.config_frame, text="RASPBERRY_ID:", font=self.custom_font)
        self.raspberry_id_label.grid_forget()  # Hide the label
        self.raspberry_id_entry = tk.Entry(self.config_frame, width=50, font=self.custom_font)
        self.raspberry_id_entry.grid_forget()  # Hide the entry

        self.filial_id_label = tk.Label(self.config_frame, text="FILIAL_ID:", font=self.custom_font)
        self.filial_id_label.grid_forget()  # Hide the label
        self.filial_id_entry = tk.Entry(self.config_frame, width=50, font=self.custom_font)
        self.filial_id_entry.grid_forget()  # Hide the entry

        self.save_config_button = tk.Button(self.config_frame, text="Salvar Configurações", command=self.save_config, font=self.custom_font)
        self.save_config_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky='w')

        # Expand all rows and columns to fill the screen
        for i in range(6):
            self.main_frame.grid_rowconfigure(i, weight=1)
        for i in range(3):
            self.main_frame.grid_columnconfigure(i, weight=1)

    def save_endpoint(self):
        new_endpoint = self.endpoint_entry.get().strip()
        if new_endpoint:
            os.environ['LARAVEL_STORE_ENDPOINT'] = new_endpoint
            with open('.env', 'r') as file:
                lines = file.readlines()
            with open('.env', 'w') as file:
                for line in lines:
                    if line.startswith('LARAVEL_STORE_ENDPOINT'):
                        file.write(f'LARAVEL_STORE_ENDPOINT={new_endpoint}\n')
                    else:
                        file.write(line)
            messagebox.showinfo("Sucesso", "Endpoint salvo com sucesso!")
        else:
            messagebox.showerror("Erro", "O endpoint não pode estar vazio.")

    def save_config(self):
        new_laravel_endpoint = self.laravel_endpoint_entry.get().strip()
        # Remove the retrieval of new_raspberry_id and new_filial_id
        # new_raspberry_id = self.raspberry_id_entry.get().strip()
        # new_filial_id = self.filial_id_entry.get().strip()

        if new_laravel_endpoint:
            os.environ['LARAVEL_STORE_ENDPOINT'] = new_laravel_endpoint
            with open('.env', 'r') as file:
                lines = file.readlines()
            with open('.env', 'w') as file:
                for line in lines:
                    if line.startswith('LARAVEL_STORE_ENDPOINT'):
                        file.write(f'LARAVEL_STORE_ENDPOINT={new_laravel_endpoint}\n')
                    # Remove the lines for RASPBERRY_ID and FILIAL_ID
                    # elif line.startswith('RASPBERRY_ID'):
                    #     file.write(f'RASPBERRY_ID={new_raspberry_id}\n')
                    # elif line.startswith('FILIAL_ID'):
                    #     file.write(f'FILIAL_ID={new_filial_id}\n')
                    else:
                        file.write(line)
            messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!")
        else:
            messagebox.showerror("Erro", "Todos os campos devem ser preenchidos.")

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
        """Exibe o MAC Address e IP da rede local no canto superior direito da janela."""
        mac_address = self.get_mac_address()
        local_network_ip = self.get_local_network_ip()
        if mac_address and local_network_ip:
            self.network_info_label.config(text=f"MAC: {mac_address}\nIP Rede Local: {local_network_ip}")

    def get_local_network_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0)
            s.connect(('192.168.1.1', 1))  # Pode ser qualquer IP na rede local
            local_network_ip = s.getsockname()[0]
            s.close()
            return local_network_ip
        except Exception as e:
            self.log(f"Erro ao obter o IP da rede local: {e}")
            return None

    def exit_fullscreen(self, event=None):
        """Sair do modo de tela cheia ao pressionar Esc ou clicar no botão."""
        self.attributes("-fullscreen", False)

    def on_closing(self):
        if messagebox.askokcancel("Sair", "Tem certeza de que deseja sair?"):
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
        timestamp = datetime.now().strftime('%H:%M')
   
        self.log_area.insert(tk.END, f"Codigo de barras batido: {barcode} - {timestamp}\n")
        self.log_area.see(tk.END)
   
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
            'mac_address': self.get_mac_address(),
            'tipo': 'online'
        }

        def send_data():
            self.barcode_status.set(f"Status: Enviando código de barras {codigobarras}...")
            if not self.is_internet_available():
                self.log("Sem conexão com a internet. Salvando no CSV.")
                self.backup_data_csv(raspberry_id, codigobarras, filial_id, data_time)
                self.failed_log_area.insert(tk.END, f"Falha ao enviar: {codigobarras} - {data_time}\n")
                self.barcode_status.set("Status: Aguardando...")
                return

            try:
                response = requests.post(f"{LARAVEL_STORE_ENDPOINT}/api/raspberry-scan-store", json=payload)
                if response.status_code == 200:
                    self.update_last_sent_timestamp(data_time)
                    self.success_log_area.insert(tk.END, f"Enviado com sucesso: {codigobarras} - {data_time}\n")
                    self.barcode_log_area_response.insert(tk.END, f"Resposta do Endpoint: {response.json()}\n")
                    self.barcode_status.set(f"Status: Código de barras {codigobarras} enviado com sucesso.")
                else:
                    self.failed_log_area.insert(tk.END, f"Erro ao enviar: {response.text}\n")
                    self.barcode_log_area_response.insert(tk.END, f"Erro do Endpoint: {response.text}\n")
                    self.backup_data_csv(raspberry_id, codigobarras, filial_id, data_time)
                    self.failed_log_area.insert(tk.END, f"Falha ao enviar: {codigobarras} - {data_time}\n")
                    self.barcode_status.set(f"Status: Falha ao enviar código de barras {codigobarras}.")
            except requests.exceptions.RequestException as e:
                self.failed_log_area.insert(tk.END, f"Erro ao tentar conectar: {e}\n")
                self.barcode_log_area_response.insert(tk.END, f"Erro ao tentar conectar: {e}\n")
                self.backup_data_csv(raspberry_id, codigobarras, filial_id, data_time)
                self.failed_log_area.insert(tk.END, f"Falha ao enviar: {codigobarras} - {data_time}\n")
                self.barcode_status.set(f"Status: Falha ao enviar código de barras {codigobarras}.")

            self.barcode_status.set("Status: Aguardando...")

        threading.Thread(target=send_data).start()

    def update_last_sent_timestamp(self, timestamp):
        self.last_sent_timestamp.set(f"Último envio: {timestamp}")
        with open('.env', 'r') as file:
            lines = file.readlines()
        with open('.env', 'w') as file:
            for line in lines:
                if line.startswith('LAST_SENT_TIMESTAMP'):
                    file.write(f'LAST_SENT_TIMESTAMP={timestamp}\n')
                else:
                    file.write(line)

    def get_last_sent_timestamp(self):
        return os.getenv('LAST_SENT_TIMESTAMP', 'Nunca')

    def is_internet_available(self):
        try:
            requests.get('https://www.google.com', timeout=5)
            return True
        except requests.ConnectionError:
            return False

    def update_failed_list(self):
        self.unsent_barcode_log_area.delete(1.0, tk.END)
        self.unsent_barcode_log_area.insert(tk.END, "Códigos de Barras Não Enviados:\n")
        for payload in self.failed_barcodes:
            self.unsent_barcode_log_area.insert(tk.END, f"{payload['codigo_barras']} - {payload['data_time']}\n")

    def backup_data_csv(self, raspberry_id, codigobarras, filial_id, data_time):
        try:
            backup_folder = '/home/kali/staf-rasp/backup'
            if not os.path.exists(backup_folder):
                os.makedirs(backup_folder)
            csv_file_path = os.path.join(backup_folder, os.path.basename(CSV_FILE_PATH))
            file_exists = os.path.isfile(csv_file_path)
            with open(csv_file_path, mode='a', newline='') as file:
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
                self.update_network_info_label()
                time.sleep(10)

        threading.Thread(target=update_status, daemon=True).start()

    def update_network_info_label(self):
        mac_address = self.get_mac_address()
        local_network_ip = self.get_local_network_ip()
        internet_status = self.internet_status_label.cget('text')
        if mac_address and local_network_ip:
            self.network_info_label.config(text=f"MAC: {mac_address}\nIP Rede Local: {local_network_ip}\n")

    def retry_failed_barcodes(self):
        pass  # Remove the retry logic

    def update_current_timestamp(self):
        self.current_timestamp.set(f"Data Hora Atual: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.after(1000, self.update_current_timestamp)

    def update_last_service_send_timestamp(self):
        last_sent = self.get_last_sent_timestamp()
        try:
            last_sent_dt = datetime.strptime(last_sent, '%d/%m/%Y %H:%M')
            next_send_dt = last_sent_dt + timedelta(hours=1)
            self.last_service_send_timestamp.set(f"Último envio: {last_sent}\nPróximo envio: {next_send_dt.strftime('%d/%m/%Y %H:%M')}")
        except ValueError:
            self.last_service_send_timestamp.set("Último envio: Nunca\nPróximo envio: Em uma hora após o primeiro envio")
        self.after(60000, self.update_last_service_send_timestamp)

    def send_csv(self):
        try:
            subprocess.run(["python", "send_csv.py"], check=True)
            self.log("CSV enviado com sucesso.")
        except subprocess.CalledProcessError as e:
            self.log(f"Erro ao enviar CSV: {e}")

    def send_all_csvs(self):
        try:
            subprocess.run(["python", "send_all_csvs.py"], check=True)
            self.log("Todos os CSVs enviados com sucesso.")
        except subprocess.CalledProcessError as e:
            self.log(f"Erro ao enviar todos os CSVs: {e}")

    def load_backup_csv(self):
        try:
            self.unsent_barcode_log_area.delete(1.0, tk.END)
            backup_folder = '/home/kali/staf-rasp/backup'
            if os.path.exists(backup_folder):
                self.unsent_barcode_log_area.insert(tk.END, "Códigos de Barras Não Enviados:\n")
                for filename in os.listdir(backup_folder):
                    if filename.endswith('.csv'):
                        backup_csv_path = os.path.join(backup_folder, filename)
                        with open(backup_csv_path, mode='r') as file:
                            reader = csv.reader(file)
                            self.unsent_barcode_log_area.insert(tk.END, f"Arquivo: {filename}\n")
                            for row in reader:
                                self.unsent_barcode_log_area.insert(tk.END, f"{row}\n")
            else:
                self.unsent_barcode_log_area.insert(tk.END, "Nenhum CSV de backup encontrado.\n")
        except Exception as e:
            self.log(f"Erro ao carregar CSV de backup: {e}")

if __name__ == "__main__":
    app = Application()
    app.check_internet_connection()  # Start checking internet connection
    app.mainloop()