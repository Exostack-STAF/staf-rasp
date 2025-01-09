#!/bin/bash

# Desativar o bloqueio de tela no GNOME
echo "Desativando o bloqueio de tela..."
gsettings set org.gnome.desktop.screensaver lock-enabled false

# Desativar o salvamento de energia da tela
echo "Desativando o salvamento de energia da tela..."
gsettings set org.gnome.desktop.session idle-delay 0

# Desativar modos de economia de energia do X11
echo "Desativando economia de energia do X11..."
xset s off
xset -dpms

# Configurar o GNOME para não escurecer a tela
echo "Impedindo o escurecimento da tela no GNOME..."
gsettings set org.gnome.settings-daemon.plugins.power sleep-display-ac 0

# Impedir a suspensão do sistema
echo "Desativando suspensão automática..."
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'

# Criar configuração para o X11 (opcional)
CONFIG_DIR="/etc/X11/xorg.conf.d"
CONFIG_FILE="$CONFIG_DIR/10-monitor.conf"
if [ ! -d "$CONFIG_DIR" ]; then
    echo "Criando diretório de configuração do X11 em $CONFIG_DIR..."
    sudo mkdir -p "$CONFIG_DIR"
fi

echo "Escrevendo configuração para impedir economia de energia no X11..."
sudo bash -c "cat > $CONFIG_FILE" << EOF
Section "ServerFlags"
    Option "BlankTime" "0"
    Option "StandbyTime" "0"
    Option "SuspendTime" "0"
    Option "OffTime" "0"
EndSection
EOF

# Garantir que as configurações sejam persistentes
echo "Adicionando configurações ao ~/.bashrc para torná-las permanentes..."
if ! grep -q "xset s off" ~/.bashrc; then
    echo "xset s off" >> ~/.bashrc
    echo "xset -dpms" >> ~/.bashrc
fi

# Recarregar o arquivo ~/.bashrc
echo "Recarregando configurações do ~/.bashrc..."
source ~/.bashrc

echo "Todas as configurações foram aplicadas com sucesso. Reinicie a sessão para garantir que tudo esteja funcionando corretamente."

sudo reboot
