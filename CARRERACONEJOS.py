import tkinter as tk
from tkinter import messagebox
import random
import time

class CarreraConejos:
    def __init__(self, root):
        self.root = root
        self.root.title("🐰 Carrera de Conejos - GAQ2")
        self.root.geometry("700x500")
        self.root.configure(bg='#f5f5f5')
        
        # Variables del juego
        self.posiciones = [0, 0]
        self.jugador_actual = 0
        self.juego_iniciado = False
        self.longitud_pista = 10
        self.rps_jugador1 = None
        
        self.crear_interfaz()
        
    def crear_interfaz(self):
        # Título
        titulo = tk.Label(
            self.root, 
            text="🐰 Carrera de Conejos 🐰",
            font=("Arial", 24, "bold"),
            bg='#f5f5f5',
            fg='#333'
        )
        titulo.pack(pady=20)
        
        subtitulo = tk.Label(
            self.root,
            text="GAQ2 - Juego para 2 jugadores",
            font=("Arial", 12),
            bg='#f5f5f5',
            fg='#666'
        )
        subtitulo.pack()
        
        # Estado del juego
        self.label_estado = tk.Label(
            self.root,
            text="Empiecen con piedra, papel o tijera",
            font=("Arial", 14, "bold"),
            bg='#e8f4f8',
            fg='#333',
            pady=10
        )
        self.label_estado.pack(pady=20, padx=20, fill='x')
        
        # Frame para piedra, papel o tijera
        self.frame_rps = tk.Frame(self.root, bg='#f5f5f5')
        self.frame_rps.pack(pady=10)
        
        self.label_rps = tk.Label(
            self.frame_rps,
            text="Jugador 1: Elige tu jugada",
            font=("Arial", 12),
            bg='#f5f5f5',
            fg='#666'
        )
        self.label_rps.pack(pady=10)
        
        frame_botones_rps = tk.Frame(self.frame_rps, bg='#f5f5f5')
        frame_botones_rps.pack()
        
        tk.Button(
            frame_botones_rps,
            text="✊ Piedra",
            font=("Arial", 14),
            width=10,
            command=lambda: self.jugar_rps('piedra')
        ).grid(row=0, column=0, padx=5)
        
        tk.Button(
            frame_botones_rps,
            text="✋ Papel",
            font=("Arial", 14),
            width=10,
            command=lambda: self.jugar_rps('papel')
        ).grid(row=0, column=1, padx=5)
        
        tk.Button(
            frame_botones_rps,
            text="✌️ Tijera",
            font=("Arial", 14),
            width=10,
            command=lambda: self.jugar_rps('tijera')
        ).grid(row=0, column=2, padx=5)
        
        # Frame del juego (oculto al inicio)
        self.frame_juego = tk.Frame(self.root, bg='#f5f5f5')
        
        # Pista del jugador 1
        frame_pista1 = tk.Frame(self.frame_juego, bg='#e3f2fd', pady=10)
        frame_pista1.pack(pady=10, padx=20, fill='x')
        
        tk.Label(
            frame_pista1,
            text="🐰 Jugador 1",
            font=("Arial", 12, "bold"),
            bg='#e3f2fd',
            fg='#1976d2'
        ).pack(side='left', padx=10)
        
        self.celdas_jugador1 = []
        frame_celdas1 = tk.Frame(frame_pista1, bg='#e3f2fd')
        frame_celdas1.pack(side='left', fill='x', expand=True)
        
        for i in range(self.longitud_pista):
            celda = tk.Label(
                frame_celdas1,
                text="",
                font=("Arial", 16),
                width=3,
                height=1,
                bg='white',
                relief='solid',
                borderwidth=1
            )
            celda.grid(row=0, column=i, padx=2)
            self.celdas_jugador1.append(celda)
        
        # Pista del jugador 2
        frame_pista2 = tk.Frame(self.frame_juego, bg='#ffebee', pady=10)
        frame_pista2.pack(pady=10, padx=20, fill='x')
        
        tk.Label(
            frame_pista2,
            text="🐰 Jugador 2",
            font=("Arial", 12, "bold"),
            bg='#ffebee',
            fg='#c62828'
        ).pack(side='left', padx=10)
        
        self.celdas_jugador2 = []
        frame_celdas2 = tk.Frame(frame_pista2, bg='#ffebee')
        frame_celdas2.pack(side='left', fill='x', expand=True)
        
        for i in range(self.longitud_pista):
            celda = tk.Label(
                frame_celdas2,
                text="",
                font=("Arial", 16),
                width=3,
                height=1,
                bg='white',
                relief='solid',
                borderwidth=1
            )
            celda.grid(row=0, column=i, padx=2)
            self.celdas_jugador2.append(celda)
        
        # Dado y botón
        frame_dado = tk.Frame(self.frame_juego, bg='#f5f5f5')
        frame_dado.pack(pady=20)
        
        self.label_dado = tk.Label(
            frame_dado,
            text="🎲",
            font=("Arial", 60),
            bg='white',
            width=3,
            height=1,
            relief='solid',
            borderwidth=2
        )
        self.label_dado.pack(pady=10)
        
        self.boton_lanzar = tk.Button(
            frame_dado,
            text="Lanzar dado",
            font=("Arial", 14, "bold"),
            bg='#4CAF50',
            fg='white',
            width=15,
            height=2,
            command=self.lanzar_dado
        )
        self.boton_lanzar.pack(pady=10)
        
        # Instrucciones
        instrucciones = tk.Label(
            self.root,
            text="Cómo jugar:\n1. Piedra, papel o tijera para ver quién empieza\n2. Túrnense lanzando el dado\n3. El dado muestra cuántos pasos avanza tu conejo\n4. El primer conejo en llegar al final gana",
            font=("Arial", 10),
            bg='#f0f0f0',
            fg='#666',
            justify='left',
            padx=15,
            pady=10
        )
        instrucciones.pack(pady=10, padx=20, fill='x')
        
    def jugar_rps(self, eleccion):
        if self.rps_jugador1 is None:
            self.rps_jugador1 = eleccion
            self.label_rps.config(text="Jugador 2: Elige tu jugada")
        else:
            eleccion_jugador2 = eleccion
            resultado = self.determinar_ganador_rps(self.rps_jugador1, eleccion_jugador2)
            
            if resultado == 0:
                self.label_estado.config(text="¡Empate! Jueguen otra vez")
                self.rps_jugador1 = None
                self.label_rps.config(text="Jugador 1: Elige tu jugada")
            else:
                self.jugador_actual = resultado - 1
                self.label_estado.config(text=f"¡Jugador {resultado} empieza!")
                self.frame_rps.pack_forget()
                self.frame_juego.pack()
                self.juego_iniciado = True
                self.actualizar_tablero()
    
    def determinar_ganador_rps(self, j1, j2):
        if j1 == j2:
            return 0
        if (j1 == 'piedra' and j2 == 'tijera') or \
           (j1 == 'papel' and j2 == 'piedra') or \
           (j1 == 'tijera' and j2 == 'papel'):
            return 1
        return 2
    
    def actualizar_tablero(self):
        # Limpiar tablero
        for celda in self.celdas_jugador1:
            celda.config(text="")
        for celda in self.celdas_jugador2:
            celda.config(text="")
        
        # Colocar conejos
        if self.posiciones[0] < self.longitud_pista:
            self.celdas_jugador1[self.posiciones[0]].config(text="🐰")
        
        if self.posiciones[1] < self.longitud_pista:
            self.celdas_jugador2[self.posiciones[1]].config(text="🐰")
    
    def lanzar_dado(self):
        if not self.juego_iniciado:
            return
        
        self.boton_lanzar.config(state='disabled')
        
        # Animación del dado
        for _ in range(10):
            numero = random.randint(1, 6)
            self.label_dado.config(text=str(numero))
            self.root.update()
            time.sleep(0.1)
        
        # Resultado final
        resultado = random.randint(1, 6)
        self.label_dado.config(text=str(resultado))
        
        self.root.after(300, lambda: self.mover_jugador(resultado))
    
    def mover_jugador(self, pasos):
        self.posiciones[self.jugador_actual] += pasos
        
        if self.posiciones[self.jugador_actual] >= self.longitud_pista:
            self.posiciones[self.jugador_actual] = self.longitud_pista
            self.actualizar_tablero()
            self.terminar_juego()
            return
        
        self.actualizar_tablero()
        self.jugador_actual = 1 if self.jugador_actual == 0 else 0
        self.label_estado.config(text=f"Turno del Jugador {self.jugador_actual + 1}")
        self.boton_lanzar.config(state='normal')
    
    def terminar_juego(self):
        self.juego_iniciado = False
        ganador = self.jugador_actual + 1
        
        respuesta = messagebox.askyesno(
            "¡Juego Terminado!",
            f"🎉 ¡Jugador {ganador} ganó! 🎉\n\n¿Quieren jugar otra vez?"
        )
        
        if respuesta:
            self.reiniciar_juego()
        else:
            self.root.quit()
    
    def reiniciar_juego(self):
        self.posiciones = [0, 0]
        self.jugador_actual = 0
        self.juego_iniciado = False
        self.rps_jugador1 = None
        
        self.label_estado.config(text="Empiecen con piedra, papel o tijera")
        self.label_rps.config(text="Jugador 1: Elige tu jugada")
        self.label_dado.config(text="🎲")
        
        self.frame_juego.pack_forget()
        self.frame_rps.pack(pady=10)
        self.boton_lanzar.config(state='normal')

if __name__ == "__main__":
    root = tk.Tk()
    juego = CarreraConejos(root)
    root.mainloop()