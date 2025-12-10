# validador_serial.py
import serial
import time

# --- Ponto de Verificação ---
# Garanta que esta porta é a mesma que o 'socat' criou no seu terminal WSL.
# O número (pts/2) pode mudar!
ARDUINO_PORT = 'COM14'
BAUD_RATE = 9600

# --- AJUSTE PRINCIPAL ---
# Este é o caminho para o seu arquivo no formato que o WSL entende.
# C:\ se torna /mnt/c/ e usamos barras normais.
FILE_PATH = r"C:\\Users\\vitor\Downloads\dados_para_arduino.txt"

try:
    arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    print(f"Validador iniciado na porta {ARDUINO_PORT}. Aguardando dados do Arduino...")

    while True:
        if arduino.in_waiting > 0:
            linha_recebida = arduino.readline().decode('utf-8').strip()
            
            # Ignora linhas vazias que podem ser recebidas
            if not linha_recebida:
                continue

            print(f"Arduino pediu para validar: [{linha_recebida}]")

            encontrado = False
            try:
                with open(FILE_PATH, 'r') as f:
                    for linha_arquivo in f:
                        if linha_arquivo.strip() == linha_recebida:
                            encontrado = True
                            break
                
                if encontrado:
                    print("--> Encontrado! Enviando 'OK'")
                    arduino.write(b'OK\n')
                else:
                    print("--> Nao encontrado! Enviando 'FAIL'")
                    arduino.write(b'FAIL\n')

            except FileNotFoundError:
                print(f"--> ERRO: Arquivo nao encontrado em '{FILE_PATH}'! Enviando 'FAIL'")
                arduino.write(b'FAIL\n')
            except Exception as e:
                print(f"--> ERRO ao ler o arquivo: {e}! Enviando 'FAIL'")
                arduino.write(b'FAIL\n')

except serial.SerialException as e:
    print(f"Ocorreu um erro fatal ao abrir a porta serial: {e}")
    print("Verifique se o 'socat' está rodando e se o nome da porta está correto.")
except Exception as e:
    print(f"Ocorreu um erro fatal: {e}")