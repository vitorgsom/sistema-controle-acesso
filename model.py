# model.py
from database import Database

class UserModel:
    def __init__(self):
        self.db = Database()

    def add_user(self, nome, cpf, senha):
        # Lógica de negócio/Validação
        if not all([nome, cpf, senha]):
            return False, "Todos os campos são obrigatórios!"
        if not (senha.isdigit() and len(senha) == 4):
            return False, "A senha deve conter exatamente 4 dígitos numéricos."
        
        # Chama o banco de dados
        return self.db.adicionar_usuario(nome, cpf, senha)

    def recover_password(self, cpf, nova_senha):
        # Lógica de negócio/Validação
        if not (nova_senha and nova_senha.isdigit() and len(nova_senha) == 4):
            return False, "Senha inválida. Deve conter 4 dígitos numéricos."
        if not cpf:
            return False, "O CPF é necessário para recuperar a senha."
            
        # Chama o banco de dados
        return self.db.recuperar_senha(cpf, nova_senha)

    def get_all_users(self):
        return self.db.get_todos_usuarios()