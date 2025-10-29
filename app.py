from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

# ---------- CREAR BASE DE DATOS ----------
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT,
                        correo TEXT,
                        rol TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS encuestas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        titulo TEXT,
                        descripcion TEXT,
                        fecha_creacion TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS preguntas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        id_encuesta INTEGER,
                        texto_pregunta TEXT,
                        tipo TEXT,
                        FOREIGN KEY(id_encuesta) REFERENCES encuestas(id))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS respuestas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        id_pregunta INTEGER,
                        id_usuario INTEGER,
                        respuesta_texto TEXT,
                        valor REAL,
                        FOREIGN KEY(id_pregunta) REFERENCES preguntas(id),
                        FOREIGN KEY(id_usuario) REFERENCES usuarios(id))''')

    conn.commit()
    conn.close()

init_db()

# ---------- RUTAS PRINCIPALES ----------

@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    encuestas = conn.execute('SELECT * FROM encuestas').fetchall()
    conn.close()
    return render_template('index.html', encuestas=encuestas)

# ---------- CREAR ENCUESTA ----------
@app.route('/crear_encuesta', methods=['GET', 'POST'])
def crear_encuesta():
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        fecha = datetime.now().strftime('%Y-%m-%d')

        conn = sqlite3.connect('database.db')
        conn.execute('INSERT INTO encuestas (titulo, descripcion, fecha_creacion) VALUES (?, ?, ?)',
                     (titulo, descripcion, fecha))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('crear_encuesta.html')

# ---------- AGREGAR PREGUNTAS ----------
@app.route('/agregar_pregunta/<int:id_encuesta>', methods=['GET', 'POST'])
def agregar_pregunta(id_encuesta):
    if request.method == 'POST':
        texto = request.form['texto']
        tipo = request.form['tipo']

        conn = sqlite3.connect('database.db')
        conn.execute('INSERT INTO preguntas (id_encuesta, texto_pregunta, tipo) VALUES (?, ?, ?)',
                     (id_encuesta, texto, tipo))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    return render_template('agregar_pregunta.html', id_encuesta=id_encuesta)

# ---------- REGISTRAR USUARIO ----------
@app.route('/registrar_usuario', methods=['GET', 'POST'])
def registrar_usuario():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        rol = request.form['rol']

        conn = sqlite3.connect('database.db')
        conn.execute('INSERT INTO usuarios (nombre, correo, rol) VALUES (?, ?, ?)', (nombre, correo, rol))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('registrar_usuario.html')

# ---------- RESPONDER ENCUESTA ----------
@app.route('/responder/<int:id_encuesta>', methods=['GET', 'POST'])
def responder(id_encuesta):
    conn = sqlite3.connect('database.db')
    preguntas = conn.execute('SELECT * FROM preguntas WHERE id_encuesta = ?', (id_encuesta,)).fetchall()
    usuarios = conn.execute('SELECT * FROM usuarios').fetchall()
    conn.close()

    if request.method == 'POST':
        id_usuario = request.form['usuario']
        conn = sqlite3.connect('database.db')
        for pregunta in preguntas:
            respuesta_texto = request.form.get(f"pregunta_{pregunta[0]}")
            valor = request.form.get(f"valor_{pregunta[0]}")
            conn.execute('INSERT INTO respuestas (id_pregunta, id_usuario, respuesta_texto, valor) VALUES (?, ?, ?, ?)',
                         (pregunta[0], id_usuario, respuesta_texto, valor))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    return render_template('responder_encuesta.html', preguntas=preguntas, usuarios=usuarios, id_encuesta=id_encuesta)

# ---------- RESULTADOS ----------
@app.route('/resultados/<int:id_encuesta>')
def resultados(id_encuesta):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Promedios para preguntas numéricas
    cursor.execute('''SELECT p.texto_pregunta, AVG(r.valor)
                      FROM respuestas r
                      JOIN preguntas p ON r.id_pregunta = p.id
                      WHERE p.id_encuesta = ? AND p.tipo = 'numero'
                      GROUP BY p.id''', (id_encuesta,))
    promedios = cursor.fetchall()

    # Respuestas textuales
    cursor.execute('''SELECT p.texto_pregunta, r.respuesta_texto, u.nombre
                      FROM respuestas r
                      JOIN preguntas p ON r.id_pregunta = p.id
                      JOIN usuarios u ON r.id_usuario = u.id
                      WHERE p.id_encuesta = ? AND p.tipo = 'texto'
                      ORDER BY p.id''', (id_encuesta,))
    textos = cursor.fetchall()

    conn.close()
    return render_template('resultados.html', promedios=promedios, textos=textos)



if __name__ == '__main__':
    app.run(debug=True)
