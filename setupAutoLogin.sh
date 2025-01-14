#!/bin/bash

USER_NAME="kali"
SCRIPT_PATH="/home/kali/staf-rasp/script.py"
SERVICE_PATH="/home/kali/staf-rasp/service.py"
WORKING_DIR="/home/kali/staf-rasp"
PYTHON_PATH="/usr/bin/python3"
SERVICE_NAME="script.service"
TIMER_NAME="python-hourly.timer"

# Create .env file if it does not exist
ENV_FILE="$WORKING_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating .env file..."
    cat > "$ENV_FILE" <<EOF
# Configurações da API
LARAVEL_STORE_ENDPOINT=https://staf-homolog.exostack.com.br
RASPBERRY_ID=1
FILIAL_ID=1

# Caminhos dos arquivos
IDS_FILE_PATH='ids.txt'
CSV_FILE_PATH='data_backup.csv'

# Timestamp do último envio
LAST_SENT_TIMESTAMP=
EOF
fi

# Enable auto-login for user kali
echo "Setting up auto-login for user $USER_NAME..."
sudo mkdir -p /etc/systemd/system/getty@tty1.service.d
sudo bash -c "cat > /etc/systemd/system/getty@tty1.service.d/override.conf <<EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $USER_NAME --noclear %I \$TERM
EOF"

# Edit LightDM configuration to enable auto-login
echo "Configuring LightDM for auto-login..."
sudo bash -c "cat >> /etc/lightdm/lightdm.conf <<EOF
[Seat:*]
autologin-user=$USER_NAME
autologin-user-timeout=0
EOF"

# Install dependencies
echo "Installing dependencies..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-tk python3-dotenv
pip3 install requests python-dotenv pynput --break-system-packages

# Create log file for service.py and set permissions
LOG_FILE="/var/log/staf_rasp_service.log"
echo "Creating log file for service.py and setting permissions..."
sudo touch $LOG_FILE
sudo chown $USER_NAME:$USER_NAME $LOG_FILE

# Create systemd service for script.py
echo "Creating systemd service for script.py..."
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
Group=$USER_NAME
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/$USER_NAME/.Xauthority

[Install]
WantedBy=default.target
EOF"

# Create systemd timer for service.py
echo "Creating systemd timer for service.py..."
sudo bash -c "cat > /etc/systemd/system/$TIMER_NAME <<EOF
[Unit]
Description=Timer to run service.py every hour

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
EOF"

# Create systemd service for service.py
SERVICE_PY_NAME="service_py.service"
echo "Creating systemd service for service.py..."
sudo bash -c "cat > /etc/systemd/system/$SERVICE_PY_NAME <<EOF
[Unit]
Description=Run service.py every hour
After=network.target

[Service]
ExecStart=$PYTHON_PATH $SERVICE_PATH
WorkingDirectory=$WORKING_DIR
User=$USER_NAME
Group=$USER_NAME
StandardOutput=append:$LOG_FILE
StandardError=append:$LOG_FILE

[Install]
WantedBy=multi-user.target
EOF"

# Disable hibernation
echo "Disabling hibernation..."
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target

# Set timezone to São Paulo
echo "Setting timezone to São Paulo..."
sudo timedatectl set-timezone America/Sao_Paulo

# Configure autostart for script.py
echo "Configuring autostart for script.py..."
mkdir -p ~/.config/autostart
sudo bash -c "cat > ~/.config/autostart/staf-rasp.desktop <<EOF
[Desktop Entry]
Type=Application
Name=STAF-RASP
Exec=python3 $SCRIPT_PATH
X-GNOME-Autostart-enabled=true
EOF"

# Ensure all .py files have execution permissions
echo "Setting execution permissions for .py files..."
chmod +x $SCRIPT_PATH
chmod +x $SERVICE_PATH

# Perform git pull on every reboot
echo "Configuring git pull on every reboot..."
sudo bash -c "cat > /etc/systemd/system/git-pull.service <<EOF
[Unit]
Description=Perform git pull on reboot
After=network.target

[Service]
ExecStart=/usr/bin/git -C $WORKING_DIR pull
WorkingDirectory=$WORKING_DIR
User=$USER_NAME
Group=$USER_NAME

[Install]
WantedBy=multi-user.target
EOF"

sudo systemctl enable git-pull.service

# Add cron job to run service.py every hour
echo "Adding cron job to run service.py every hour..."
(crontab -l 2>/dev/null; echo "0 * * * * /usr/bin/python3 /home/kali/staf-rasp/service.py") | crontab -

# Reload systemd and enable services
echo "Reloading systemd and enabling services..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME
sudo systemctl enable $TIMER_NAME
sudo systemctl start $TIMER_NAME
sudo systemctl enable $SERVICE_PY_NAME

echo "Setup completed. Rebooting the system..."
sudo reboot
