from bson.objectid import ObjectId
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = "pec_secreto_2024"

# Configuración de subida de archivos
app.config["UPLOAD_FOLDER"] = "static/evidencias"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Conexión MongoDB
uri = "mongodb+srv://cujb081019hmcrsra9_db_user:pollo12345@cluster0.tayz8f9.mongodb.net/?appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi("1"), tls=True, tlsAllowInvalidCertificates=True)
db = client["PEC"]
actividades = db["Actividades"]
usuarios_col = db["Usuarios"]
sedes_col = db["Sedes"]

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class Usuario(UserMixin):
    def __init__(self, data):
        self.id = str(data["_id"])
        self.nombre = data["nombre"]
        self.rol = data["rol"]

@login_manager.user_loader
def cargar_usuario(user_id):
    datos = usuarios_col.find_one({"_id": ObjectId(user_id)})
    if datos:
        return Usuario(datos)
    return None

# Decorador solo admin (corregido con .lower())
def solo_admin(f):
    @wraps(f)
    def decorador(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol.lower() != "admin":
            flash("Acceso denegado. Solo administradores.")
            return redirect(url_for("ver_actividades"))
        return f(*args, **kwargs)
    return decorador

# Registro
@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":

        nombre = request.form["nombre"].strip()
        password = request.form["password"]
        rol = request.form["rol"].lower()

        # Verificar que el usuario no exista
        if usuarios_col.find_one({"nombre": nombre}):
            flash("Ese nombre de usuario ya existe.")
            return redirect(url_for("registro"))

        # Solo estos roles pueden registrarse
        if rol not in ["encargado", "alumno", "ciudadano"]:
            flash("Rol no válido.")
            return redirect(url_for("registro"))

        usuarios_col.insert_one({
            "nombre": nombre,
            "password": generate_password_hash(password),
            "rol": rol
        })

        flash("Usuario registrado correctamente.")
        return redirect(url_for("login"))

    return render_template("registro.html")

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        nombre = request.form["nombre"]
        password = request.form["password"]
        tipo_usuario = request.form["tipo_usuario"]

        usuario = usuarios_col.find_one({
            "nombre": nombre,
            "rol": tipo_usuario.lower()
        })

        if usuario and check_password_hash(usuario["password"], password):
            login_user(Usuario(usuario))
            return redirect(url_for("index"))

        flash("Usuario o contraseña incorrectos.")

    return render_template("login.html")
# Login de administrador
@app.route("/login_admin", methods=["POST"])
def login_admin():

    password = request.form["password"]

    usuario = usuarios_col.find_one({"nombre": "admin"})

    if usuario and check_password_hash(usuario["password"], password):
        login_user(Usuario(usuario))
        return redirect(url_for("index"))

    flash("Contraseña de administrador incorrecta.")
    return redirect(url_for("login"))
# Logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# Inicio con estadísticas (todos)
@app.route("/")
@login_required
def index():
    total = actividades.count_documents({})
    completadas = actividades.count_documents({"estado": "completada"})
    pendientes = actividades.count_documents({"estado": "pendiente"})
    en_proceso = actividades.count_documents({"estado": "en_proceso"})
    return render_template(
        "index.html",
        total=total,
        completadas=completadas,
        pendientes=pendientes,
        programadas=en_proceso
    )

# Agregar actividad (solo admin)
@app.route("/agregar_actividad", methods=["GET", "POST"])
@login_required
@solo_admin
def agregar_actividad():
    if request.method == "POST":

        archivos = request.files.getlist("evidencias[]")
        nombres = []

        for file in archivos:
            if file and file.filename:
                filename = file.filename
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                nombres.append(filename)

        sede = request.form.get("sede")

        if sede == "Otra":
            otra = request.form.get("otra_sede", "").strip()
            sede = otra if otra else "No especificada"

        nueva = {
            "numero": request.form["numero"],
            "nombre": request.form["nombre"],
            "descripcion": request.form["descripcion"],
            "responsable": request.form["responsable"],
            "fecha": request.form["fecha"],
            "sede": sede,
            "evidencias": nombres,
            "estado": request.form["estado"]
        }

        actividades.insert_one(nueva)
        flash("Actividad agregada correctamente.")
        return redirect(url_for("ver_actividades"))

    sedes = list(sedes_col.find({"activo": True}))

    return render_template(
        "agregar_actividad.html",
        sedes=sedes
    )
# Ver actividades (todos)
@app.route("/actividades")
@login_required
def ver_actividades():
    lista = list(actividades.find())
    return render_template("actividades.html", actividades=lista)

# Editar actividad (solo admin)
@app.route("/editar_actividad/<id>", methods=["GET", "POST"])
@login_required
@solo_admin
def editar_actividad(id):

    actividad = actividades.find_one({"_id": ObjectId(id)})

    if request.method == "POST":

        sede = request.form["sede"]

        if sede == "Otra":
            sede = request.form["otra_sede"]

        datos = {
            "numero": request.form["numero"],
            "nombre": request.form["nombre"],
            "descripcion": request.form["descripcion"],
            "responsable": request.form["responsable"],
            "fecha": request.form["fecha"],
            "sede": sede,
            "estado": request.form["estado"]
        }

        archivos = request.files.getlist("evidencias[]")
        nombres = actividad.get("evidencias") or []
        for file in archivos:
            if file and file.filename:
                filename = file.filename
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                nombres.append(filename)

        datos["evidencias"] = nombres

        actividades.update_one(
            {"_id": ObjectId(id)},
            {"$set": datos}
        )

        flash("Actividad editada correctamente.")
        return redirect(url_for("ver_actividades"))

    return render_template(
        "editar_actividad.html",
        actividad=actividad
    )

# Eliminar actividad (solo admin)
@app.route("/eliminar_actividad/<id>")
@login_required
@solo_admin
def eliminar_actividad(id):
    actividades.delete_one({"_id": ObjectId(id)})
    flash("Actividad eliminada correctamente.")
    return redirect(url_for("ver_actividades"))

# Buscar actividad (todos)
@app.route("/buscar_actividad", methods=["GET", "POST"])
@login_required
def buscar_actividad():
    resultados = []
    mensaje = ""
    if request.method == "POST":
        campo = request.form["campo"]
        valor = request.form["valor"].strip()
        resultados = list(actividades.find({
            campo: {"$regex": valor, "$options": "i"}
        }))
        if not resultados:
            mensaje = "No se encontraron actividades."
    return render_template("buscar_actividad.html", resultados=resultados, mensaje=mensaje)

# Reportes (solo admin)
@app.route("/reportes")
@login_required
@solo_admin
def reportes():
    total = actividades.count_documents({})
    completadas = actividades.count_documents({"estado": "completada"})
    pendientes = actividades.count_documents({"estado": "pendiente"})
    en_proceso = actividades.count_documents({"estado": "en_proceso"})
    lista = list(actividades.find())
    return render_template(
        "reportes.html",
        total=total,
        completadas=completadas,
        pendientes=pendientes,
        en_proceso=en_proceso,
        actividades=lista
    )

if __name__ == "__main__":
    app.run(debug=True)