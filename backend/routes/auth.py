from flask import Blueprint, request, jsonify

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    # Aqui entraria a lógica de validação com o banco de dados
    return jsonify({"message": "Login realizado com sucesso", "user": data.get('email')}), 200

@auth_bp.route('/register', methods=['POST'])
def register():
    return jsonify({"message": "Usuário registrado"}), 201