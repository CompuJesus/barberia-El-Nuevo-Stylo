# Agrega render_template a los imports de flask
from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import os
from datetime import datetime
import io
import pandas as pd
from flask import send_file
from fpdf import FPDF

app = Flask(__name__)

# Conexión a MongoDB Atlas (La clave se esconde por seguridad)
# Si estás probando en tu PC, puedes usar una variable de entorno local o colocar tu URI aquí temporalmente
MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["barberia_db"]
coleccion_facturacion = db["facturacion"]

# Modifica la ruta inicial para que muestre el archivo HTML
@app.route('/', methods=['GET'])
def inicio():
    return render_template('index.html')

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
# Ruta para descargar el Excel
@app.route('/api/exportar/excel', methods=['GET'])
def exportar_excel():
    # Traemos todos los cortes de Mongo, ocultando el ID interno que genera ruido en Excel
    cortes = list(coleccion_facturacion.find({}, {"_id": 0}))
    
    if not cortes:
        return "No hay datos para exportar", 404

    # Convertimos los datos a una tabla de Pandas
    df = pd.DataFrame(cortes)
    
    # Formateamos la fecha para que se lea limpia en el Excel
    if 'fecha_hora' in df.columns:
        df['fecha_hora'] = df['fecha_hora'].dt.strftime('%Y-%m-%d %H:%M')

    # Creamos el archivo Excel directamente en la memoria del servidor
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Facturacion')
    
    output.seek(0)
    return send_file(output, download_name="Reporte_Barberia.xlsx", as_attachment=True)

# Ruta para descargar el PDF
@app.route('/api/exportar/pdf', methods=['GET'])
def exportar_pdf():
    cortes = list(coleccion_facturacion.find({}, {"_id": 0}))
    
    # Configuramos el PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    
    # Título del documento
    pdf.set_font("helvetica", style="B", size=16)
    pdf.cell(0, 10, text="Reporte de Ventas - Barbería", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10) # Salto de línea
    
    # Cuerpo del PDF
    pdf.set_font("helvetica", size=10)
    if not cortes:
        pdf.cell(0, 10, text="No hay datos registrados aún.", new_x="LMARGIN", new_y="NEXT")
    else:
        for corte in cortes:
            # Extraemos la información limpiando si hay algo vacío
            fecha = corte.get('fecha_hora').strftime('%Y-%m-%d') if corte.get('fecha_hora') else 'S/F'
            cliente = corte.get('cliente', 'N/A')
            servicio = corte.get('servicio', 'N/A')
            monto = corte.get('monto_cobrado', 0)
            pago = corte.get('metodo_pago', 'N/A')
            
            linea_texto = f"{fecha} | {cliente} | {servicio} | {pago} | ${monto}"
            pdf.cell(0, 8, text=linea_texto, new_x="LMARGIN", new_y="NEXT")
            
    # Guardamos en memoria y enviamos al navegador
    output = io.BytesIO(pdf.output())
    return send_file(output, download_name="Reporte_Barberia.pdf", as_attachment=True, mimetype='application/pdf')
    
if __name__ == '__main__':
    # El puerto 5000 es el estándar de Flask para pruebas locales
    app.run(debug=True, host='0.0.0.0', port=5000)
