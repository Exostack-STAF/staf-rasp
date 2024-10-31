#!/bin/bash

echo "Iniciando a instalação do aplicativo..."

# Atualizar o sistema
echo "Atualizando o sistema..."
sudo apt update && sudo apt upgrade -y

# Instalar Python e dependências
echo "Instalando Python e bibliotecas necessárias..."
sudo apt install python3 python3-pip -y
pip3 install requests python-dotenv

echo "Instalação concluída com sucesso!"
