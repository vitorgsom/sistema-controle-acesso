# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_socketio import SocketIO, emit
from model import UserModel
import webbrowser
from threading import Timer
import serial
import serial.tools.list_ports
import time

# --- Configuração ---
app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_super_segura' 
# O socketio é o nosso novo 'cérebro' de comunicação em tempo real
# Forçamos o async_mode='threading' para evitar erros no PyInstaller
socketio = SocketIO(app, async_mode='threading')

# --- Rotas da Aplicação ---

@app.route('/', methods=['GET', 'POST'])
def index():
    """ Rota principal para cadastrar usuários. """
    if request.method == 'POST':
        model = UserModel()
        nome = request.form.get('nome')
        cpf = request.form.get('cpf')
        senha = request.form.get('senha')
        success, message = model.add_user(nome, cpf, senha)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
        return redirect(url_for('index'))
    return render_template('index.html')

@app.route('/usuarios')
def ver_usuarios():
    """ Rota para visualizar a lista de usuários. """
    model = UserModel()
    usuarios = model.get_all_users()
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/recuperar', methods=['GET', 'POST'])
def recuperar_senha():
    """ Rota para a recuperação de senha. """
    if request.method == 'POST':
        model = UserModel()
        cpf = request.form.get('cpf')
        nova_senha = request.form.get('nova_senha')
        success, message = model.recover_password(cpf, nova_senha)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
        return redirect(url_for('recuperar_senha'))
    return render_template('recuperar.html')

@app.route('/exportar')
def exportar():
    """ Renderiza a página de sincronização interativa. """
    return render_template('exportar.html')

# --- HANDLERS DO SOCKETIO ---

@socketio.on('connect')
def handle_connect():
    """ Evento disparado quando o navegador se conecta. """
    print('Cliente conectado ao SocketIO')
    emit('log_update', {'msg': 'Conectado ao servidor. Clique em "Listar Portas" para começar.'})

@socketio.on('listar_portas_request')
def handle_listar_portas():
    """ Ouve o pedido 'listar_portas_request'. """
    emit('log_update', {'msg': 'Procurando TODAS as portas seriais...'})
    try:
        ports = serial.tools.list_ports.comports()
        port_list = []
        
        # Lista TODAS as portas encontradas sem filtro
        for p in ports:
            port_list.append({'device': p.device, 'description': p.description})
        
        if not port_list:
            emit('log_update', {'msg': 'Nenhuma porta serial COM foi encontrada.'})
            emit('log_update', {'msg': '--> Verifique se a ESP32 está conectada.'})
        else:
            emit('log_update', {'msg': f'Encontradas {len(port_list)} portas. Selecione a correta abaixo.'})
        
        emit('listar_portas_response', port_list)
        
    except Exception as e:
        emit('log_update', {'msg': f'ERRO ao listar portas: {str(e)}'})


@socketio.on('sincronizar_request')
def handle_sincronizar(data):
    """ 
    Ouve o pedido 'sincronizar_request'.
    Configurado especificamente para ESP32: 115200 baud e tratamento de reset.
    """
    port_selecionada = data['port']
    if not port_selecionada:
        emit('log_update', {'msg': 'ERRO: Nenhuma porta selecionada.'})
        return

    emit('log_update', {'msg': f'Iniciando sincronização com {port_selecionada} a 115200 baud...'})
    
    arduino = None
    try:
        # 1. Obter dados do banco de dados
        model = UserModel()
        usuarios = model.get_all_users()
        if not usuarios:
            emit('log_update', {'msg': 'Nenhum usuário no banco de dados para enviar.'})
            return
            
        emit('log_update', {'msg': f'Encontrados {len(usuarios)} usuários para sincronizar.'})
        
        # 2. Conectar à ESP32 (Tentativa Robusta de evitar problemas de boot)
        emit('log_update', {'msg': 'Abrindo conexão serial...'})
        
        # Configuração manual para evitar o pulso DTR/RTS
        arduino = serial.Serial()
        arduino.port = port_selecionada
        arduino.baudrate = 115200 # Velocidade do Bootloader da ESP32
        arduino.timeout = 15
        arduino.dtr = False
        arduino.rts = False
        
        arduino.open()
        
        # Limpeza de Lixo (Caso tenha resetado e o bootloader tenha falado)
        time.sleep(0.5) 
        arduino.reset_input_buffer() 
        
        # 3. Iniciar Handshake (Handshake 1)
        emit('log_update', {'msg': 'Enviando comando: SYNC_START'})
        arduino.write(b"SYNC_START\n")
        
        # 4. Esperar Arduino ficar pronto (Handshake 2)
        emit('log_update', {'msg': 'Aguardando sinal "READY_TO_LOAD"...'})
        
        # Lê a resposta e remove espaços em branco
        resposta = arduino.readline().decode('utf-8', errors='ignore').strip()
        
        if resposta != "READY_TO_LOAD":
            # Se recebeu lixo ou timeout
            emit('log_update', {'msg': f'ERRO: Falha no handshake. Respondeu: "{resposta}"'})
            emit('log_update', {'msg': '--> DICA: Tente novamente. Se persistir, pressione o botão BOOT na ESP32.'})
            arduino.close()
            return
        
        emit('log_update', {'msg': 'ESP32 pronta. Enviando matrículas...'})

        # 5. Enviar dados (Matrículas)
        for matricula, senha, nome in usuarios:
            matricula_para_enviar = matricula
            arduino.write(matricula_para_enviar.encode() + b'\n')
            emit('log_update', {'msg': f'Enviando: {matricula_para_enviar}'})
            time.sleep(0.02) # Pequeno delay

        # 6. Finalizar (Handshake 3)
        arduino.write(b"END_DATA_LOAD\n")
        emit('log_update', {'msg': 'Sinal de finalização enviado. Aguardando confirmação...'})
        
        # 7. Esperar Confirmação (Handshake 4)
        resposta_final = arduino.readline().decode('utf-8', errors='ignore').strip()
        
        if resposta_final == "LOAD_OK":
            emit('log_update', {'msg': '--- Sincronização concluída com sucesso! ---'})
        else:
            emit('log_update', {'msg': f'--- ERRO: Sem confirmação final. Resposta: "{resposta_final}" ---'})

    except serial.SerialException as e:
        if "PermissionError" in str(e):
            emit('log_update', {'msg': f'ERRO: Acesso negado à porta {port_selecionada}.'})
            emit('log_update', {'msg': '--> Verifique se o Monitor Serial do Arduino IDE está aberto e FECHE-O.'})
        else:
            emit('log_update', {'msg': f'ERRO Serial: {str(e)}'})
    except Exception as e:
        emit('log_update', {'msg': f'ERRO Inesperado: {str(e)}'})
    finally:
        if arduino and arduino.is_open:
            arduino.close()
            emit('log_update', {'msg': 'Conexão fechada.'})

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

# Altere o bloco final para:
if __name__ == '__main__':
    print("Iniciando servidor Flask-SocketIO...")
    Timer(1.5, open_browser).start() # Abre o navegador após 1.5s
    # O debug deve ser False em produção para evitar erros com PyInstaller
    socketio.run(app, debug=False, allow_unsafe_werkzeug=True)