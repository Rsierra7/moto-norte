from utils.window_manager import abrir_ventana, center_window
import tkinter as tk
import subprocess
# import threading
import os
import sys

procesos = {
    "inventario": None,
    "ventas": None,
    "reporte_inv": None,
    "reporte_venta": None
}

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # cuando es .exe
    except Exception:
        base_path = os.path.abspath(".")  # cuando es .py

    return os.path.join(base_path, relative_path)

BASE_PATH = os.path.dirname(resource_path(""))

def ejecutar(script):
    ruta = os.path.join(BASE_PATH, script)

    if getattr(sys, 'frozen', False):
        subprocess.run([ruta])  # ejecuta .exe
    else:
        subprocess.run(["python", ruta])

#def ejecutar_async(script):
#    threading.Thread(target=ejecutar, args=(script,), daemon=True).start()

root = tk.Tk()
root.title("🏍️ Moto Norte")
center_window(root, 300, 400)
root.config(bg="#2c3e50")

imagen = tk.PhotoImage(file=resource_path("pngegg.png"))
label_imagen = tk.Label(root, image=imagen)
label_imagen.pack(pady=10)
label_imagen.config(bg="#2c3e50")

frame_botones = tk.Frame(root, bg="#2c3e50")
frame_botones.pack(pady=10)

tk.Button(frame_botones, text="\n Inventario \n", bg="#27ae60", fg="white", command=lambda: abrir_ventana(root, "ui/inventario.pyw"), width=32).grid(row=2, column=0, columnspan=2, padx=2, pady=10)
tk.Button(frame_botones, text="\n Ventas \n", bg="#27ae60", fg="white", command=lambda: abrir_ventana(root, "ui/venta.pyw"), width=32).grid(row=3, column=0, columnspan=2, padx=2, pady=10)
# tk.Button(root, text="Reporte Inventario", bg="#27ae60", fg="white", command=lambda: ejecutar_async("ui\\reporte_inv.pyw")).pack(pady=5)
tk.Button(frame_botones, text="\n Reporte Ventas \n", bg="#27ae60", fg="white", command=lambda: abrir_ventana(root, "ui/reporte_venta.pyw"), width=32).grid(row=4, column=0, columnspan=2, padx=2, pady=10)

root.mainloop()