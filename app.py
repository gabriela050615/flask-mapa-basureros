from flask import Flask, render_template, jsonify, request
import os
import mysql.connector
from urllib.parse import urlparse

# Obtener la URL de la base de datos desde las variables de entorno
db_url = os.getenv("DB_URL")
parsed_url = urlparse(db_url)

# Extraer las credenciales de la URL
config = {
    'user': parsed_url.username,  # Usuario
    'password': parsed_url.password,  # Contraseña
    'host': parsed_url.hostname,  # Host
    'port': parsed_url.port,  # Puerto
    'database': parsed_url.path[1:],  # Nombre de la base de datos
}

# Conectar a MySQL
conexion = mysql.connector.connect(**config)

# 🔹 Ruta principal que carga el mapa
@app.route("/")
def mostrar_mapa():
    return render_template("mapa.html")  # Asegúrate de que `mapa.html` está en `templates/`

# 🔹 API para obtener los basureros desde MySQL
@app.route("/api/basureros", methods=["GET"])
def get_basureros():
    try:
        conexion = mysql.connector.connect(**db_config)
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT BASURERO_ID, LATITUD, LONGITUD, ESTADO FROM DATOS;")
        basureros = cursor.fetchall()
        cursor.close()
        conexion.close()
        return jsonify(basureros)  # Devuelve los datos en JSON
    except mysql.connector.Error as e:
        return jsonify({"error": f"Error al conectar con MySQL: {e}"})

# 🔹 API para calcular la ruta óptima con Dijkstra
@app.route("/api/ruta", methods=["GET"])
def calcular_ruta():
    considerar_medio = request.args.get("medio") == "true"

    try:
        # Conexión a la base de datos
        conexion = mysql.connector.connect(**db_config)
        cursor = conexion.cursor(dictionary=True)

        # Consulta basureros dependiendo del parámetro "medio"
        if considerar_medio:
            cursor.execute("SELECT BASURERO_ID, LATITUD, LONGITUD FROM DATOS WHERE ESTADO IN ('LLENO', 'MEDIO');")
        else:
            cursor.execute("SELECT BASURERO_ID, LATITUD, LONGITUD FROM DATOS WHERE ESTADO = 'LLENO';")

        basureros = cursor.fetchall()
        cursor.close()
        conexion.close()

        # Si no hay suficientes basureros, devolver error
        if len(basureros) < 2:
            return jsonify({"error": "No hay suficientes basureros para calcular una ruta"}), 400

        # Construcción del grafo
        G = nx.Graph()
        nodos = []
        for b in basureros:
            nodo = (b["BASURERO_ID"], b["LATITUD"], b["LONGITUD"])
            nodos.append(nodo)
            G.add_node(nodo)

        # Crear conexiones entre nodos con distancia euclidiana
        for i in range(len(nodos)):
            for j in range(i + 1, len(nodos)):
                distancia = ((nodos[i][1] - nodos[j][1]) ** 2 + (nodos[i][2] - nodos[j][2]) ** 2) ** 0.5
                G.add_edge(nodos[i], nodos[j], weight=distancia)

        # Calcular la ruta óptima con Dijkstra
        inicio = nodos[0]
        ruta = nx.shortest_path(G, source=inicio, weight="weight")

        # Convertir la ruta a un formato JSON válido
        ruta_json = [{"BASURERO_ID": n[0], "LATITUD": n[1], "LONGITUD": n[2]} for n in ruta]

        return jsonify({"ruta": ruta_json})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
if __name__ == "__main__":
    app.run(debug=True)
