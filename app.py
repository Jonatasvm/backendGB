from flask import Flask
from flask_cors import CORS

# Importação das Rotas
from routes.auth_routes import auth_bp
from routes.obras_routes import obras_bp
from routes.usuarios_routes import usuarios_bp
from routes.formulario_routes import formulario_bp
from routes.banks_routes import bancos_bp
from routes.fornecedor_routes import fornecedor_bp
from routes.export_routes import export_bp

def create_app():
    app = Flask(__name__)

    # CORS mais leve e igualmente funcional
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Registrar rotas
    app.register_blueprint(auth_bp)
    app.register_blueprint(obras_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(formulario_bp)
    app.register_blueprint(bancos_bp)
    app.register_blueprint(fornecedor_bp)
    app.register_blueprint(export_bp)

    return app

if __name__ == "__main__":
    app = create_app()

    # RODE ASSIM PARA VELOCIDADE MÁXIMA:f
    app.run(
        host="0.0.0.0",   # Muito mais rápido que 0.0.0.0 no Windows
        port=5631,          # Porta leve, não exige privilégios
        debug=False,        # Evita duplicação de processo
        use_reloader=False  # Evita lentidão do watchdog
    )
