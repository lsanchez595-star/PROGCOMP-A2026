import hashlib
import time
import random

# Usuario: admin
# Contraseña: Admin123!
USERS = {
    "admin": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a"
}

# --------------------------------------------------
# FUNCIÓN HASH
# --------------------------------------------------
def sha256(s):
    return hashlib.sha256(s.encode()).hexdigest()

# --------------------------------------------------
# VALIDAR CONTRASEÑA
# --------------------------------------------------
def validar_password(pwd):
    errores = []

    # Mínimo 8 caracteres
    if len(pwd) < 8:
        errores.append("Mínimo 8 caracteres")

    # Al menos una mayúscula
    if not any(c.isupper() for c in pwd):
        errores.append("Al menos 1 mayúscula")


    # Al menos una minúscula
    if not any(c.islower() for c in pwd):
        errores.append("Al menos 1 minúscula")

    # Al menos un número
    if not any(c.isdigit() for c in pwd):
        errores.append("Al menos 1 número")

    # Al menos un carácter especial
    if not any(c in "!@#$%^&*()" for c in pwd):
        errores.append("Al menos 1 especial (!@#$%^&*())")

    # No permitir espacios
    if " " in pwd:
        errores.append("No se permiten espacios")

    return errores

# --------------------------------------------------
# CAPTCHA
# --------------------------------------------------
def captcha():
    a = random.randint(1, 20)
    b = random.randint(1, 10)

    r = input(f"CAPTCHA → ¿Cuánto es {a} + {b}? ").strip()

    return r.isdigit() and int(r) == a + b

# --------------------------------------------------
# LOGIN
# --------------------------------------------------
def login():

    intentos = 3
    bloqueado_hasta = 0

    print("=" * 40)
    print("      LOGIN ANTI-BOBOS")
    print("=" * 40)

    while True:

        # Verificar bloqueo
        if time.time() < bloqueado_hasta:
            restante = int(bloqueado_hasta - time.time())

            print(f"\n Sistema bloqueado.")
            print(f"Espera {restante} segundos...\n")

            time.sleep(1)
            continue

        # Usuario
        user = input("\nUsuario: ").strip()

        if not user:
            print("El usuario no puede estar vacío.\n")
            continue

        # CAPTCHA
        print("\nVerificación humana:")
        if not captcha():
            print("CAPTCHA incorrecto.\n")
            continue

        # Contraseña
        pwd = input("\nContraseña: ").strip()

        errores = validar_password(pwd)

        # Mostrar errores
        if errores:
            print("\n La contraseña no cumple con:")
            for e in errores:
                print(f" • {e}")
            print()
            continue

        # Verificar login
        if USERS.get(user) == sha256(pwd):

            print("\n ACCESO CONCEDIDO")
            print(f" Bienvenido, {user}")

            break

        else:
            intentos -= 1

            print(f"\n Credenciales incorrectas.")
            print(f" Intentos restantes: {intentos}")

            # Bloqueo temporal
            if intentos == 0:

                bloqueado_hasta = time.time() + 30
                intentos = 3

                print("\n Demasiados intentos fallidos.")
                print(" Sistema bloqueado por 30 segundos.\n")

# --------------------------------------------------
# EJECUTAR
# --------------------------------------------------
login()