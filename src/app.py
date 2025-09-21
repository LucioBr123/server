from flask import Flask
from flask_cors import CORS
from routes.routes import setup_routes
import sys

sys.dont_write_bytecode = True  # Desativa geração de .pyc

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config['JSON_SORT_KEYS'] = False  # Para não ordenar os JSONs
    setup_routes(app)
    return app

# Só executa se for chamado diretamente
if __name__ == '__main__':
    from waitress import serve
    app = create_app()
    print("Servidor rodando na rede local em http://0.0.0.0:5000")
    serve(app, host='0.0.0.0', port=5000)