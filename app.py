from flask import Flask, request, jsonify
from pymongo import MongoClient
import os
from datetime import datetime

app = Flask(__name__)

# Conexión a MongoDB Atlas (La clave se esconde por seguridad)
# Si estás probando en tu PC, puedes usar una variable de entorno local o colocar tu URI aquí temporalmente
MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["barberia_db"]
coleccion_facturacion = db["facturacion"]

@app.route('/', methods=['GET'])
def inicio():
    return "¡El sistema de la barbería está en línea!"

# Ruta para registrar un nuevo corte
@app.route('/api/nueva_venta', methods=['POST'])
def registrar_venta():
    datos = request.json
    nueva_venta = {
        "fecha_hora": datetime.now(),
        "servicio": datos.get("servicio"),
        "cliente": datos.get("cliente", "Cliente Frecuente"),
        "metodo_pago": datos.get("metodo_pago"),
        "monto_cobrado": datos.get("monto_cobrado")
    }

    resultado = coleccion_facturacion.insert_one(nueva_venta)
    return jsonify({"mensaje": "Corte registrado con éxito", "id": str(resultado.inserted_id)}), 201

# Ruta para ver todos los cortes registrados
@app.route('/api/ventas', methods=['GET'])
def obtener_ventas():
    ventas = []
    # Buscamos todos los documentos en la colección
    for venta in coleccion_facturacion.find():
        venta["_id"] = str(venta["_id"]) # Convertimos el ID de Mongo a texto
        ventas.append(venta)

    return jsonify(ventas), 200

if __name__ == '__main__':
    # El puerto 5000 es el estándar de Flask para pruebas locales
    app.run(debug=True, host='0.0.0.0', port=5000)
