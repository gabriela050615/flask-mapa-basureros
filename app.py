from flask import Flask, render_template, jsonify, request
import mysql.connector
from urllib.parse import urlparse

app = Flask(__name__)

# 🔹 Configuración de la base de datos en Railway
DB_URL = "mysql://root:evQpLNMiCpQYHPUKDOfDOrerHqLQNHbg@autorack.proxy.rlwy.net:55608/railway"
parsed_url = urlparse(DB_URL)

config = {
    'user': parsed_url.username,
    'password': parsed_url.password,
    'host': parsed_url.hostname,
    'port': parsed_url.port,
    'database': parsed_url.path[1:],  # Quita la barra inicial
}

def get_db_connection():
    """Establece la conexión con la base de datos Railway."""
    return mysql.connector.connect(**config)

# 🔹 Ruta principal: Muestra el mapa
@app.route("/")
def mostrar_mapa():
    return render_template("mapa.html")  # Asegúrate de que `mapa.html` está en `templates/`

# 🔹 API para obtener los basureros
@app.route("/api/basureros", methods=["GET"])
def get_basureros():
    try:
        conexion = get_db_connection()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT BASURERO_ID, LATITUD, LONGITUD, ESTADO FROM DATOS;")
        basureros = cursor.fetchall()
        return jsonify(basureros)
    except mysql.connector.Error as e:
        return jsonify({"error": f"Error al conectar con MySQL: {e}"})
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()

# 🔹 API para calcular la ruta con Dijkstra
@app.route("/api/ruta", methods=["GET"])
def calcular_ruta():
    incluir_medios = request.args.get("medio", "false").lower() == "true"

    try:
        conexion = get_db_connection()
        cursor = conexion.cursor(dictionary=True)

        # 🔹 Obtener los basureros necesarios según el estado
        estado_query = "('LLENO')" if not incluir_medios else "('LLENO', 'MEDIO')"
        cursor.execute(f"SELECT BASURERO_ID, LATITUD, LONGITUD FROM DATOS WHERE ESTADO IN {estado_query};")
        puntos = cursor.fetchall()

        if not puntos:
            return jsonify({"error": "No hay basureros en el estado seleccionado."})

        # 🔹 Simulación del cálculo de ruta usando Dijkstra (implementación real pendiente)
        ruta = sorted(puntos, key=lambda x: x['LATITUD'])  # Ordenado como ejemplo

        return jsonify({"ruta": ruta})

    except mysql.connector.Error as e:
        return jsonify({"error": f"Error al calcular la ruta: {e}"})
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()

if __name__ == "__main__":
    app.run(debug=True)
