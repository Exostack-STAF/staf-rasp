#!/bin/bash

# Variáveis
SERVICE_NAME="script.service"
TIMER_NAME="python-hourly.timer"
SCRIPT_PATH="/home/kali/staf-rasp/script.py"
USER_NAME="kali"
GROUP_NAME="kali"
WORKING_DIR="/home/kali/staf-rasp"
PYTHON_PATH="/usr/bin/python3"

# Verifica se o script existe
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Erro: O script $SCRIPT_PATH não foi encontrado."
    exit 1
fi

# Cria o arquivo de serviço
echo "Criando o arquivo de serviço systemd..."
sudo bash -c "cat > /etc/systemd/system/$SERVICE_NAME <<EOF
[Unit]
Description=Start script.py with Tkinter after login
After=graphical.target

[Service]
ExecStartPre=/usr/bin/git -C $WORKING_DIR pull
ExecStart=$PYTHON_PATH $SCRIPT_PATH
WorkingDirectory=$WORKING_DIR
Restart=always
User=$USER_NAME
Group=$GROUP_NAME
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/$USER_NAME/.Xauthority

[Install]
WantedBy=default.target
EOF"

# Cria o arquivo de timer
TIMER_FILE="/etc/systemd/system/$TIMER_NAME"
echo "Criando o arquivo de timer em $TIMER_FILE..."
sudo bash -c "cat > $TIMER_FILE <<EOF
[Unit]
Description=Timer para rodar script Python de hora em hora

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
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

# Habilita e inicia o timer
echo "Ativando o timer..."
sudo systemctl enable "$TIMER_NAME"
echo "Iniciando o timer..."
sudo systemctl start "$TIMER_NAME"

# Verifica o status do serviço
echo "Verificando o status do serviço..."
sudo systemctl status "$SERVICE_NAME"

echo "Configuração concluída!"
echo "Você pode verificar o status do timer com: systemctl list-timers --all"
