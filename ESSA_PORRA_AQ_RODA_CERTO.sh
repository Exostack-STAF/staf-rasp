/bin/bash
# PIOR CODIGO DE 2024 - BOA SORTE - LELE, BERTIN E PBUM 02-11-2024 -> TODO DIA SAI UMA MALANDRO E UM OTARIO DE CASA.
ENDPOINT="https://stsm.exostack.com.br/api/raspberry-scan-store"
RASP_ID=1  # Substitua pelo ID do Raspberry Pi
FILIAL_ID=1  # Substitua pelo ID da filial
# HELLO WORD
echo "Aguardando leitura do código de barras..."
while true; do
    # Captura o código de barras do scanner
    read -r CODIGO  # Captura o input do scanner
    # Captura a data e hora atual
    DATETIME=$(date '+%Y-%m-%d %H:%M:%S')
    # Envia o código de barras e outros dados para o endpoint
    curl -X POST -H "Content-Type: application/json" \
         -d "{\"codigo_barras\":\"$CODIGO\", \"data_time\":\"$DATETIME\", \"raspberry_id\":\"$RASP_ID\", \"filial_id\":\"$FILIAL_ID\"}" \
         $ENDPOINT
    # FIZ ISSO CHAPADO DE CERVEJA VIVA OCKTOBERFEST 
done
