import io
import xlsxwriter
from flask import Flask, request, jsonify, render_template, send_file
from pymongo import MongoClient
from fpdf import FPDF
import os
from datetime import datetime

app = Flask(__name__)

# Configuración de base de datos
MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["barberia_db"]
coleccion_facturacion = db["facturacion"]

# --- RUTAS DE LA PÁGINA ---

@app.route('/', methods=['GET'])
def inicio():
    return render_template('index.html')

# --- RUTAS DE API ---

@app.route('/api/nueva_venta', methods=['POST'])
def registrar_venta():
    datos = request.json
    nueva_venta = {
        "fecha_hora": datetime.now(),
        "servicio": datos.get("servicio"),
        "cliente": datos.get("cliente", "Cliente"),
        "metodo_pago": datos.get("metodo_pago"),
        "monto_cobrado": datos.get("monto_cobrado"),
        "referencia": datos.get("referencia", "")
    }
    coleccion_facturacion.insert_one(nueva_venta)
    return jsonify({"mensaje": "Éxito"}), 201

# --- RUTAS DE EXPORTACIÓN ---

@app.route('/api/exportar/excel', methods=['GET'])
def exportar_excel():
    cortes = list(coleccion_facturacion.find({}, {"_id": 0}))
    if not cortes: return "No hay datos", 404

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()
    
    # Encabezados
    headers = ["Fecha", "Cliente", "Servicio", "Pago", "Referencia", "Monto"]
    for col, head in enumerate(headers): worksheet.write(0, col, head)
        
    # Filas
    for row, c in enumerate(cortes, start=1):
        worksheet.write(row, 0, str(c.get('fecha_hora', '')))
        worksheet.write(row, 1, c.get('cliente', ''))
        worksheet.write(row, 2, c.get('servicio', ''))
        worksheet.write(row, 3, c.get('metodo_pago', ''))
        worksheet.write(row, 4, c.get('referencia', ''))
        worksheet.write(row, 5, c.get('monto_cobrado', 0))
            
    workbook.close()
    output.seek(0)
    return send_file(output, download_name="Reporte_Ventas.xlsx", as_attachment=True)

@app.route('/api/exportar/pdf', methods=['GET'])
def exportar_pdf():
    cortes = list(coleccion_facturacion.find({}, {"_id": 0}))
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Reporte de Cortes - Barbería", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    pdf.set_font("helvetica", size=10)
    for c in cortes:
        linea = f"{c.get('fecha_hora')} | {c.get('cliente')} | {c.get('servicio')} | ${c.get('monto_cobrado')}"
        pdf.cell(0, 8, linea, new_x="LMARGIN", new_y="NEXT")
            
    output = io.BytesIO(pdf.output())
    return send_file(output, download_name="Reporte_Ventas.pdf", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
