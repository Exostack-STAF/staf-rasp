#!/bin/bash

# Variáveis
SERVICE_NAME="script.service"
SCRIPT_PATH="/home/kali/staf-rasp/script.py"
USER_NAME="kali"
WORKING_DIR="/home/kali/staf-rasp"

# Verifica se o script existe
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Erro: O script $SCRIPT_PATH não foi encontrado."
    exit 1
fi

# Cria o arquivo de serviço
echo "Criando o arquivo de serviço systemd..."
sudo bash -c "cat > /etc/systemd/system/$SERVICE_NAME <<EOF
[Unit]
Description=Start script.py after login
After=multi-user.target

[Service]
ExecStart=/usr/bin/python3 $SCRIPT_PATH
WorkingDirectory=$WORKING_DIR
Restart=always
User=$USER_NAME

[Install]
WantedBy=default.target
EOF"

# Ajusta permissões do script
echo "Tornando o script executável..."
chmod +x "$SCRIPT_PATH"

# Recarrega o systemd
echo "Recarregando o daemon systemd..."
sudo systemctl daemon-reload

# Habilita o serviço para iniciar automaticamente no login
echo "Ativando o serviço para iniciar automaticamente..."
sudo systemctl enable "$SERVICE_NAME"

# Inicia o serviço
echo "Iniciando o serviço..."
sudo systemctl start "$SERVICE_NAME"

# Verifica o status do serviço
echo "Verificando o status do serviço..."
sudo systemctl status "$SERVICE_NAME"

echo "Configuração concluída!"
