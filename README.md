# STMF-RASP

**STMF-RASP** é um projeto desenvolvido para rodar um script Python em um Raspberry Pi. O script é executado automaticamente na inicialização do sistema e opera em tela cheia no terminal LXDE, realizando tarefas de validação, conexão com um banco de dados MySQL e backup de dados.

## Funcionalidades

- **Validação do Raspberry Pi:** Verifica o endereço MAC e o IP público do Raspberry Pi.
- **Geração e Envio de Chave SSH:** Cria uma chave SSH se não existir e a envia para um servidor remoto.
- **Conexão com MySQL:** Conecta-se a um banco de dados MySQL e insere dados sobre códigos de barras.
- **Backup de Dados:** Salva dados localmente em um arquivo CSV em caso de erro na inserção no banco de dados.
- **Execução Automática:** Configura o Raspberry Pi para executar o script em tela cheia automaticamente após o boot.

## Requisitos

- **Raspberry Pi:** Qualquer modelo com suporte a Raspbian.
- **Python 3.x:** Instalado no Raspberry Pi.
- **Bibliotecas Python:** `requests`, `mysql-connector-python`
- **MySQL Server:** Configurado e acessível a partir do Raspberry Pi.
- **Arquivo `.env`:** Para armazenar dados sensíveis.

## Configuração

### 1. Preparar o Ambiente

1. **Instalar Dependências:**

    Certifique-se de ter as bibliotecas Python necessárias instaladas:

    ```bash
    pip install requests mysql-connector-python
    ```

2. **Configurar o Arquivo `.env`:**

    Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:

    ```plaintext
    LARAVEL_VALIDATE_ENDPOINT=http://192.168.1.10:8000/api/verify-raspberry
    LARAVEL_STATUS_ENDPOINT=http://192.168.1.10:8000/api/raspberry-status
    LARAVEL_SSH_KEY_ENDPOINT=http://192.168.1.10:8000/api/raspberry-ssh-key
    MYSQL_HOST=localhost
    MYSQL_DATABASE=EXOSTACK-STMF
    MYSQL_USER=root
    MYSQL_PASSWORD=Pedro1997
    IDS_FILE_PATH=ids.txt
    CSV_FILE_PATH=data_backup.csv
    ```

### 2. Configurar o Script de Inicialização

O script `STMF-RASP.sh` já está incluído no repositório. Este script configura o terminal em tela cheia e executa o programa.

1. **Tornar o Script Executável:**

    Certifique-se de que o script tem permissões de execução:

    ```bash
    chmod +x ~/STMF-RASP.sh
    ```

2. **Configurar o Script para Inicializar Automaticamente:**

    - **Usando `crontab`:**

        Abra o crontab para edição:

        ```bash
        crontab -e
        ```

        Adicione a linha para executar o script ao iniciar o sistema:

        ```bash
        @reboot /home/pi/STMF-RASP.sh
        ```

    - **Usando `autostart`:**

        Edite o arquivo `autostart` do LXDE:

        ```bash
        nano ~/.config/lxsession/LXDE-pi/autostart
        ```

        Adicione a linha para executar o script ao iniciar a sessão LXDE:

        ```bash
        @/home/pi/STMF-RASP.sh
        ```

### 3. Executar o Script Manualmente

Para testar o script manualmente, execute:

```bash
bash ~/STMF-RASP.sh
```

## Estrutura do Projeto

- `STMF-RASP.sh`: Script de inicialização que configura o terminal em tela cheia e executa o programa.
- `dist/main`: Executável Python (gerado a partir do código-fonte).
- `.env`: Arquivo de configuração com dados sensíveis (não incluído no repositório).

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para fazer um fork do repositório e enviar pull requests. Para maiores informações sobre como contribuir, consulte o [guia de contribuição](CONTRIBUTING.md).

## Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

sudo apt install xrdp
# staf-rasp
