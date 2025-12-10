import sqlite3
import bcrypt
from datetime import datetime

class Database:
    def __init__(self, db_file="usuarios.db"):
        """Inicializa a conexão com o banco de dados e cria a tabela se não existir."""
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self._criar_tabela()

    def _criar_tabela(self):
        """Cria a tabela de usuários se ela ainda não existe."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_completo TEXT NOT NULL,
                cpf_hash TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                matricula TEXT UNIQUE NOT NULL
            )
        """)
        self.conn.commit()

    def _gerar_matricula(self):
            """
            Gera uma matrícula sequencial única de no máximo 4 caracteres.
            Ex: 0001, 0002, ..., 9999
            """
            # Procura a matrícula mais alta no banco de dados
            # Usamos CAST(matricula AS INTEGER) para garantir que '10' venha depois de '9'
            self.cursor.execute(
                "SELECT matricula FROM usuarios ORDER BY CAST(matricula AS INTEGER) DESC LIMIT 1"
            )
            ultima_matricula = self.cursor.fetchone()
            
            sequencial = 1 # Começa do 1 se o banco estiver vazio
            if ultima_matricula:
                # Converte a última matrícula (ex: '0009') para um inteiro (9) e soma 1
                sequencial = int(ultima_matricula[0]) + 1
                
                if sequencial > 9999:
                    # Tratamento de erro caso o limite de 4 caracteres seja atingido
                    print("Erro: Limite de matrículas (9999) atingido.")
                    # Você pode retornar um erro aqui ou lidar como preferir
                    # Retornar "ERRO" impedirá o cadastro
                    return "ERRO" 
                    
            # Formata o número para ter 4 dígitos, preenchendo com zeros à esquerda
            # Ex: 1 -> "0001", 99 -> "0099"
            return f"{sequencial:04d}"

    def cpf_existe(self, cpf):
        """Verifica se um CPF já existe no banco de dados."""
        self.cursor.execute("SELECT cpf_hash FROM usuarios")
        todos_hashes = self.cursor.fetchall()
        for cpf_hash in todos_hashes:
            if bcrypt.checkpw(cpf.encode('utf-8'), cpf_hash[0].encode('utf-8')):
                return True
        return False

    def adicionar_usuario(self, nome, cpf, senha):
        """Adiciona um novo usuário ao banco de dados."""
        if self.cpf_existe(cpf):
            print("Erro: CPF já cadastrado.")
            return False, "CPF já cadastrado."

        # Criptografa o CPF com bcrypt
        cpf_hash = bcrypt.hashpw(cpf.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Gera a matrícula
        matricula = self._gerar_matricula()

        try:
            self.cursor.execute(
                "INSERT INTO usuarios (nome_completo, cpf_hash, senha, matricula) VALUES (?, ?, ?, ?)",
                (nome, cpf_hash, senha, matricula)
            )
            self.conn.commit()
            print(f"Usuário {nome} adicionado com matrícula {matricula}.")
            return True, f"Usuário cadastrado com matrícula: {matricula}"
        except sqlite3.Error as e:
            print(f"Erro ao inserir usuário: {e}")
            return False, f"Erro no banco de dados: {e}"

    def recuperar_senha(self, cpf, nova_senha):
        """Atualiza a senha de um usuário a partir do CPF."""
        # Precisamos encontrar o ID do usuário pelo CPF
        self.cursor.execute("SELECT id, cpf_hash FROM usuarios")
        usuario_id = None
        for id_db, cpf_hash in self.cursor.fetchall():
            if bcrypt.checkpw(cpf.encode('utf-8'), cpf_hash.encode('utf-8')):
                usuario_id = id_db
                break
        
        if not usuario_id:
            return False, "CPF não encontrado."

        # Atualiza a senha usando o ID encontrado
        self.cursor.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (nova_senha, usuario_id))
        self.conn.commit()
        return True, "Senha alterada com sucesso!"
        
    def get_todos_usuarios(self):
        """Retorna uma lista de todos os usuários (matrícula e senha)."""
        self.cursor.execute("SELECT matricula, senha, nome_completo FROM usuarios ORDER BY nome_completo")
        return self.cursor.fetchall()

    def __del__(self):
        """Fecha a conexão com o banco de dados ao destruir o objeto."""
        self.conn.close()