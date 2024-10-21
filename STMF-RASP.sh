#!/bin/bash

# Diretório onde o script está localizado
SCRIPT_DIR="$(dirname "$(realpath "$0")")"

# Caminho para o executável dentro do diretório dist
EXECUTABLE="${SCRIPT_DIR}/dist/script"

# Verifica se o arquivo existe
if [ -f "$EXECUTABLE" ]; then
    # Torna o executável um programa executável
    chmod +x "$EXECUTABLE"
    # Executa o programa
    "$EXECUTABLE"
else
    echo "Erro: O executável não foi encontrado em $EXECUTABLE"
    exit 1
fi
