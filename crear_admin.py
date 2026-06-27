<<<<<<< HEAD
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

uri = "mongodb+srv://cujb081019hmcrsra9_db_user:pollo12345@cluster0.tayz8f9.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri)
db = client["PEC"]
usuarios_col = db["Usuarios"]

usuarios_col.delete_one({"nombre": "admin"})  # borrar admin viejo

usuarios_col.insert_one({
    "nombre": "admin",
    "password": generate_password_hash("admin123"),
    "rol": "admin"
})

=======
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

uri = "mongodb+srv://cujb081019hmcrsra9_db_user:pollo12345@cluster0.tayz8f9.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri)
db = client["PEC"]
usuarios_col = db["Usuarios"]

usuarios_col.delete_one({"nombre": "admin"})  # borrar admin viejo

usuarios_col.insert_one({
    "nombre": "admin",
    "password": generate_password_hash("admin123"),
    "rol": "admin"
})

>>>>>>> 54ab0fa72fb786001a55ca123c612201e6593459
print("✅ Admin recreado con contraseña admin123")