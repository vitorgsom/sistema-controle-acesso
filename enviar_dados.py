# enviar_matriculas.py
import serial
import time

# --- Configure suas portas aqui ---
# MUDE AQUI: Aponte para a Porta NATIVA (ex: COM15)
ARDUINO_PORT = 'COM17' 
BAUD_RATE = 9600
# O arquivo gerado pelo seu app Flask
FILE_PATH = r"C:\Users\vitor\Downloads\dados_para_arduino.txt" 
# --- Fim da Configuração ---

print(f"Iniciando sincronização com a porta NATIVA {ARDUINO_PORT}...")
print("O Arduino NÃO deve resetar.")

try:
    # --- AJUSTE CRUCIAL ---
    # dsrdtr=False impede que o pyserial cause o reset na porta nativa
    arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=5, dsrdtr=False)
    time.sleep(1) 
    
    # 1. Envia o comando de início de sincronização
    print("Enviando comando de início: SYNC_START")
    arduino.write(b"SYNC_START\n")
    
    # 2. Espera o Arduino dizer que está pronto
    resposta = arduino.readline().decode().strip()
    if resposta != "READY_FOR_DATA":
        print(f"Erro: Arduino respondeu com '{resposta}' em vez de 'READY_FOR_DATA'")
        arduino.close()
        exit()
        
    print("Arduino está pronto. Lendo arquivo de dados...")
    
    # 3. Envia os dados (matrículas)
    count = 0
    with open(FILE_PATH, 'r') as f:
        for linha in f:
            linha = linha.strip()
            if linha:
                matricula = linha.split(',')[0]
                print(f"Enviando: {matricula}")
                arduino.write(matricula.encode() + b'\n')
                count += 1
                time.sleep(0.01)
    
    # 4. Envia o sinal de "fim de transmissão"
    arduino.write(b"END_DATA_LOAD\n")
    print("Dados enviados. Aguardando confirmação final...")
    
    # 5. Espera o "LOAD_OK" final
    resposta_final = arduino.readline().decode().strip()
    if resposta_final == "LOAD_OK":
        print(f"\nSincronização concluída! {count} matrículas enviadas.")
    else:
        print(f"Erro na confirmação final. Arduino disse: {resposta_final}")

    arduino.close()

except serial.SerialException as e:
    print(f"Erro: Não foi possível abrir a porta serial: {e}")
    print("Verifique se a porta COM NATIVA está correta e se não está em uso.")
except Exception as e:
    print(f"Ocorreu um erro: {e}")