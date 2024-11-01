#!/bin/bash

# Atualiza o gerenciador de pacotes
echo "Atualizando o gerenciador de pacotes..."
sudo apt-get update

# Instala o Python3 e o pip, se não estiverem instalados
echo "Instalando Python e pip..."
sudo apt-get install -y python3 python3-pip

# Instala as bibliotecas necessárias
echo "Instalando as bibliotecas necessárias..."
pip3 install requests python-dotenv pynput --break-system-packages

# Verifica se o tkinter já está instalado
if ! dpkg -l | grep -q python3-tk; then
    echo "Instalando tkinter..."
    sudo apt-get install -y python3-tk
else
    echo "tkinter já está instalado."
fi

echo "Instalação concluída!"
