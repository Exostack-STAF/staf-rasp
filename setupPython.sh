#!/bin/bash

# Configurações
SERVICE_NAME="python-hourly"
SCRIPT_PATH="/home/kali/staf-rasp/script.py"
USER="kali"
GROUP="kali"
PYTHON_PATH="/usr/bin/python3"

# Verificar se o script Python existe
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Erro: O script Python não foi encontrado em $SCRIPT_PATH"
    exit 1
fi

# Criar arquivo de serviço
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
echo "Criando o arquivo de serviço em $SERVICE_FILE..."
cat <<EOL | sudo tee $SERVICE_FILE > /dev/null
[Unit]
Description=Executar script Python de hora em hora
After=network.target

[Service]
Type=oneshot
ExecStart=${PYTHON_PATH} ${SCRIPT_PATH}
WorkingDirectory=$(dirname $SCRIPT_PATH)
StandardOutput=journal
StandardError=journal
User=${USER}
Group=${GROUP}

[Install]
WantedBy=multi-user.target
EOL

# Criar arquivo de timer
TIMER_FILE="/etc/systemd/system/${SERVICE_NAME}.timer"
echo "Criando o arquivo de timer em $TIMER_FILE..."
cat <<EOL | sudo tee $TIMER_FILE > /dev/null
[Unit]
Description=Timer para rodar script Python de hora em hora

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
EOL

# Recarregar o systemd e ativar o timer
echo "Recarregando o systemd..."
sudo systemctl daemon-reload

echo "Ativando o timer..."
sudo systemctl enable ${SERVICE_NAME}.timer

echo "Iniciando o timer..."
sudo systemctl start ${SERVICE_NAME}.timer

echo "Configuração concluída!"
echo "Você pode verificar o status com: systemctl list-timers --all"
