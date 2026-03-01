from flask import Blueprint, request, jsonify
from services.user_service import authenticate, register_user
from flask_cors import cross_origin

auth_bp = Blueprint("auth", __name__)

# ---------------------------
# REGISTER
# ---------------------------
@auth_bp.route("/register", methods=["POST", "OPTIONS"])
@cross_origin()
def register():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    data = request.get_json()

    usuario = data.get("usuario")
    password = data.get("password")
    role = data.get("role", "user")
    nome = data.get("nome", "")
    
    # IMPORTANTE: Captura as obras enviadas pelo Frontend
    obras = data.get("obras", []) 

    if not usuario or not password:
        return jsonify({"error": "Campos incompletos"}), 400

    # Passa as obras para o serviço
    new_user, error = register_user(usuario, password, role, obras, nome)

    if error:
        return jsonify({"error": error}), 409

    return jsonify({
        "message": "Usuário criado com sucesso",
        "usuario": new_user["username"],
        "nome": new_user["nome"],
        "role": new_user["role"],
        "obras": new_user["obras"],
        "token": new_user["token"]
    }), 201

# ---------------------------
# LOGIN
# ---------------------------
@auth_bp.route("/login", methods=["POST", "OPTIONS"])
@cross_origin()
def login():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    data = request.get_json()
    usuario = data.get("usuario")
    password = data.get("password")

    if not usuario or not password:
        return jsonify({"error": "Campos incompletos"}), 400

    user, error = authenticate(usuario, password)

    if error:
        return jsonify({"error": error}), 401

    return jsonify({
        "id": user["id"],
        "usuario": user["username"],
        "nome": user.get("nome", ""),
        "role": user["role"],
        "token": user["token"]
    }), 200