import tkinter as tk
import random

# tamaño del tablero
FILAS = 10
COLUMNAS = 10
MINAS = 15

# colores para los numeros
colores = {
    1: "blue",
    2: "green",
    3: "red",
    4: "purple",
    5: "maroon",
    6: "cyan",
    7: "black",
    8: "gray"
}

class Buscaminas:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Buscaminas")
        self.ventana.resizable(False, False)

        self.modo = None  # "jugador" o "computadora"
        self.juego_terminado = False

        # guardar los botones y el estado
        self.botones = []
        self.minas_pos = []
        self.descubierto = []
        self.marcado = []
        self.numeros = []

        self.mostrar_menu()
        self.ventana.mainloop()

    def mostrar_menu(self):
        # limpiar ventana
        for widget in self.ventana.winfo_children():
            widget.destroy()

        frame = tk.Frame(self.ventana, bg="#c0c0c0", padx=30, pady=30)
        frame.pack()

        tk.Label(frame, text="BUSCAMINAS", font=("Arial", 20, "bold"),
                 bg="#c0c0c0").pack(pady=10)

        tk.Label(frame, text="Elige modo de juego:", font=("Arial", 12),
                 bg="#c0c0c0").pack(pady=5)

        tk.Button(frame, text="Jugar vs Computadora", width=20,
                  font=("Arial", 11),
                  command=lambda: self.iniciar_juego("computadora"),
                  bg="#d4d0c8", relief="raised").pack(pady=5)

        tk.Button(frame, text="Jugar 2 Jugadores", width=20,
                  font=("Arial", 11),
                  command=lambda: self.iniciar_juego("jugador"),
                  bg="#d4d0c8", relief="raised").pack(pady=5)

        tk.Label(frame, text="(en 2 jugadores se turnan en la misma PC)",
                 font=("Arial", 9), bg="#c0c0c0", fg="gray").pack(pady=2)

    def iniciar_juego(self, modo):
        self.modo = modo
        self.juego_terminado = False
        self.botones = []
        self.descubierto = [[False]*COLUMNAS for _ in range(FILAS)]
        self.marcado = [[False]*COLUMNAS for _ in range(FILAS)]
        self.numeros = [[0]*COLUMNAS for _ in range(FILAS)]
        self.turno_jugador = 1  # para modo 2 jugadores
        self.puntos = [0, 0]  # puntos jugador 1 y 2

        # poner minas aleatorias
        self.minas_pos = []
        while len(self.minas_pos) < MINAS:
            f = random.randint(0, FILAS - 1)
            c = random.randint(0, COLUMNAS - 1)
            if (f, c) not in self.minas_pos:
                self.minas_pos.append((f, c))

        # calcular numeros
        for f, c in self.minas_pos:
            for df in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nf = f + df
                    nc = c + dc
                    if 0 <= nf < FILAS and 0 <= nc < COLUMNAS:
                        if (nf, nc) not in self.minas_pos:
                            self.numeros[nf][nc] += 1

        self.construir_tablero()

    def construir_tablero(self):
        # limpiar ventana
        for widget in self.ventana.winfo_children():
            widget.destroy()

        # barra de arriba
        top = tk.Frame(self.ventana, bg="#c0c0c0", pady=5)
        top.pack(fill="x")

        self.label_info = tk.Label(top, text=self.get_info_texto(),
                                   font=("Arial", 10), bg="#c0c0c0")
        self.label_info.pack(side="left", padx=10)

        tk.Button(top, text="Reiniciar", command=lambda: self.iniciar_juego(self.modo),
                  bg="#d4d0c8", font=("Arial", 9)).pack(side="right", padx=5)

        tk.Button(top, text="Menu", command=self.mostrar_menu,
                  bg="#d4d0c8", font=("Arial", 9)).pack(side="right", padx=5)

        # el tablero con botones
        frame_tablero = tk.Frame(self.ventana, bg="#808080", padx=3, pady=3)
        frame_tablero.pack()

        for f in range(FILAS):
            fila_botones = []
            for c in range(COLUMNAS):
                btn = tk.Button(frame_tablero, width=2, height=1,
                                font=("Arial", 9, "bold"),
                                bg="#c0c0c0", relief="raised",
                                bd=2)
                # guardar posicion en el boton usando lambda con default arg
                btn.bind("<Button-1>", lambda e, fila=f, col=c: self.click_izq(fila, col))
                btn.bind("<Button-3>", lambda e, fila=f, col=c: self.click_der(fila, col))
                btn.grid(row=f, column=c, padx=1, pady=1)
                fila_botones.append(btn)
            self.botones.append(fila_botones)

        # si es vs computadora, hacer primer movimiento automatico despues de un segundo
        if self.modo == "computadora":
            self.ventana.after(500, self.turno_computadora_hint)

    def get_info_texto(self):
        if self.modo == "jugador":
            return f"Turno: Jugador {self.turno_jugador}  |  J1: {self.puntos[0]} pts  J2: {self.puntos[1]} pts"
        else:
            return f"Minas: {MINAS}  |  Marcadas: {self.contar_marcadas()}"

    def contar_marcadas(self):
        total = 0
        for f in range(FILAS):
            for c in range(COLUMNAS):
                if self.marcado[f][c]:
                    total += 1
        return total

    def click_izq(self, f, c):
        if self.juego_terminado:
            return
        if self.marcado[f][c] or self.descubierto[f][c]:
            return

        if (f, c) in self.minas_pos:
            # boom
            self.mostrar_todas_minas()
            self.botones[f][c].config(bg="red", text="💣")
            self.juego_terminado = True

            if self.modo == "jugador":
                ganador = 2 if self.turno_jugador == 1 else 1
                tk.messagebox.showinfo("Boom!", f"💥 Jugador {self.turno_jugador} pisó una mina!\nGana Jugador {ganador}!")
            else:
                tk.messagebox.showinfo("Boom!", "💥 Pisaste una mina! Game Over")
        else:
            # descubrir celda
            if self.modo == "jugador":
                self.puntos[self.turno_jugador - 1] += 1

            self.descubrir(f, c)
            self.label_info.config(text=self.get_info_texto())

            # cambiar turno en modo 2 jugadores
            if self.modo == "jugador":
                self.turno_jugador = 2 if self.turno_jugador == 1 else 1
                self.label_info.config(text=self.get_info_texto())

            self.verificar_victoria()

    def click_der(self, f, c):
        if self.juego_terminado or self.descubierto[f][c]:
            return
        if self.marcado[f][c]:
            self.marcado[f][c] = False
            self.botones[f][c].config(text="", bg="#c0c0c0")
        else:
            self.marcado[f][c] = True
            self.botones[f][c].config(text="🚩", bg="#c0c0c0")
        self.label_info.config(text=self.get_info_texto())

    def descubrir(self, f, c):
        # si ya fue descubierta o esta marcada no hacer nada
        if self.descubierto[f][c] or self.marcado[f][c]:
            return
        self.descubierto[f][c] = True
        num = self.numeros[f][c]
        btn = self.botones[f][c]
        btn.config(relief="sunken", bg="#d4d0c8")

        if num > 0:
            color = colores.get(num, "black")
            btn.config(text=str(num), fg=color)
        else:
            btn.config(text="")
            # si es 0 descubrir vecinos automaticamente
            for df in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nf = f + df
                    nc = c + dc
                    if 0 <= nf < FILAS and 0 <= nc < COLUMNAS:
                        if not self.descubierto[nf][nc]:
                            self.descubrir(nf, nc)

    def mostrar_todas_minas(self):
        for f, c in self.minas_pos:
            if not self.marcado[f][c]:
                self.botones[f][c].config(text="💣", bg="#ff9999", relief="sunken")

    def verificar_victoria(self):
        celdas_sin_mina = FILAS * COLUMNAS - MINAS
        descubiertas = 0
        for f in range(FILAS):
            for c in range(COLUMNAS):
                if self.descubierto[f][c]:
                    descubiertas += 1
        if descubiertas >= celdas_sin_mina:
            self.juego_terminado = True
            if self.modo == "jugador":
                if self.puntos[0] > self.puntos[1]:
                    msg = f"🎉 Gana Jugador 1!\nJ1: {self.puntos[0]} pts  J2: {self.puntos[1]} pts"
                elif self.puntos[1] > self.puntos[0]:
                    msg = f"🎉 Gana Jugador 2!\nJ1: {self.puntos[0]} pts  J2: {self.puntos[1]} pts"
                else:
                    msg = f"🤝 Empate!\nJ1: {self.puntos[0]} pts  J2: {self.puntos[1]} pts"
                tk.messagebox.showinfo("¡Ganaron!", msg)
            else:
                tk.messagebox.showinfo("¡Ganaste!", "🎉 Encontraste todas las celdas seguras!")

    # la computadora hace movimientos aleatorios cada 2 segundos
    def turno_computadora_hint(self):
        pass  # solo avisa que el jugador empieza

    def computadora_jugar(self):
        if self.juego_terminado:
            return
        # buscar celdas no descubiertas y no marcadas
        opciones = []
        for f in range(FILAS):
            for c in range(COLUMNAS):
                if not self.descubierto[f][c] and not self.marcado[f][c]:
                    opciones.append((f, c))

        if not opciones:
            return

        # la computadora elige al azar (no es muy lista jaja)
        f, c = random.choice(opciones)

        if (f, c) in self.minas_pos:
            self.mostrar_todas_minas()
            self.botones[f][c].config(bg="red", text="💣")
            self.juego_terminado = True
            tk.messagebox.showinfo("Computadora perdió", "💻 La computadora pisó una mina!\n¡Tú ganas!")
        else:
            self.descubrir(f, c)
            self.verificar_victoria()


# necesario para el messagebox
import tkinter.messagebox

# iniciar el juego
juego = Buscaminas()