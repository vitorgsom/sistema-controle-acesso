# Sistema de Controle de Acesso Autônomo com ESP32

Projeto de TCC desenvolvido para validação de credenciais em memória com sincronização via Serial.

## Tecnologias
- Python 3
- Flask & SocketIO
- ESP32 (C++)
- SQLite

# Sistema de Controle de Acesso com Sincronização ESP32

Este projeto é um sistema web desenvolvido em **Python (Flask)** para gerenciamento de usuários e controle de acesso autônomo. Sua principal funcionalidade é gerenciar credenciais (matrículas e senhas) e sincronizá-las diretamente para a memória de um microcontrolador **ESP32** via comunicação Serial, permitindo que o dispositivo funcione offline.

## 🚀 Funcionalidades

### Gestão Web (Dashboard)
- **Cadastro de Usuários**: Registro de Nome, CPF e Senha (4 dígitos).
  - *Geração Automática de Matrícula*: O sistema gera matrículas sequenciais (ex: 0001, 0002).
  - *Segurança*: O CPF é armazenado como hash (bcrypt) para privacidade.
- **Painel de Usuários**: Visualização de todos os usuários cadastrados e suas credenciais.
- **Recuperação de Senha**: Permite redefinir a senha numérica validando o CPF original.

### Integração com Hardware (ESP32)
- **Sincronização Serial**: Interface web dedicada para enviar dados ao ESP32.
- **Logs em Tempo Real**: Utiliza **WebSockets (SocketIO)** para mostrar o progresso da comunicação serial na tela do navegador (ex: "Porta encontrada", "Enviando usuário X", "Sucesso").
- **Protocolo de Handshake**: Implementa um protocolo robusto de comunicação para garantir a integridade dos dados:
  1. PC envia: `SYNC_START`
  2. ESP32 responde: `READY_TO_LOAD`
  3. PC envia lista de matrículas...
  4. PC finaliza: `END_DATA_LOAD`
  5. ESP32 confirma: `LOAD_OK`

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python 3, Flask.
- **Comunicação Real-Time**: Flask-SocketIO.
- **Hardware/Serial**: PySerial (configurado para 115200 baud, padrão ESP32).
- **Banco de Dados**: SQLite (simples e eficiente para este escopo).
- **Frontend**: HTML5, CSS3, Jinja2 Templates.

## 📂 Estrutura do Projeto

- `app.py`: Arquivo principal. Gerencia as rotas web, a conexão SocketIO e a lógica de comunicação Serial.
- `database.py`: Camada de persistência. Gerencia conexão SQLite, criação de tabelas e queries.
- `model.py`: Camada de regras de negócio (validações de senha, verificação de CPF duplicado).
- `validador.py` e `enviar_dados.py`: Scripts utilitários para testes manuais de comunicação serial.
- `templates/`: Arquivos HTML do frontend.
- `static/`: Arquivos CSS e assets.

## ⚙️ Instalação e Execução

1. **Clone o repositório**:
   ```bash
   git clone https://github.com/vitorgsom/sistema-controle-acesso.git
   cd sistema-controle-acesso
2. **Crie e ative um ambiente virtual(Recomendado)**:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
3. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
4. **Execute a aplicação**:
   ```bash
   python app.py
5. **Acesse no navegador**: Abra http://localhost:5000

## 🔌 Como Sincronizar com a ESP32

1. Conecte a ESP32 à porta USB do computador.
2. No menu do sistema, vá em "Sincronizar Arduino".
3. Clique em "Listar Portas" para identificar a porta COM disponível.
4. Selecione a porta correta e clique em "Sincronizar".
5. Acompanhe o log na tela ("Terminal") até ver a mensagem de sucesso.

```Nota: Certifique-se de que o Monitor Serial da Arduino IDE esteja FECHADO antes de iniciar a sincronização, para evitar conflito de porta (PermissionError).```