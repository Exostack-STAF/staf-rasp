#!/bin/bash

USER_NAME="kali"
SCRIPT_PATH="/home/kali/staf-rasp/script.py"
SERVICE_PATH="/home/kali/staf-rasp/service.py"
WORKING_DIR="/home/kali/staf-rasp"
PYTHON_PATH="/usr/bin/python3"
SERVICE_NAME="script.service"
TIMER_NAME="python-hourly.timer"

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

# Ensure script.py has execution permissions
echo "Setting execution permissions for script.py..."
chmod +x $SCRIPT_PATH

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
