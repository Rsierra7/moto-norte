import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.filedialog import asksaveasfilename
# import csv
from datetime import datetime
from services import inventario_service as service
from services.reportes_service import export_to_csv
from utils.window_manager import *

def cargar():
    table.delete(*table.get_children())
    data = service.fetch_inventory()

    for row in data:
        table.insert("", tk.END, values=row)

def export_inventory_to_csv():
    fecha = datetime.now().strftime("%d_%m_%y")
    nombre = f"Inventario_Moto_Norte_{fecha}.csv"
    
    # Definir encabezados específicos
    headers = ["CODIGO", "PRODUCTO", "UBICACION", "PRECIO", "CANTIDAD", "TOTAL"]
    
    # Extraer datos de la tabla (usando tu variable 'table')
    data = [table.item(row)["values"] for row in table.get_children()]
    
    # Llamar al servicio genérico
    export_to_csv(nombre, headers, data)

# UI
root = tk.Tk()
root.title("📊 Reporte Inventario")
root.config(bg="#2c3e50")
center_window(root, 800, 400)

# tk.Button(root, text="\nActualizar\n", command=cargar).pack(padx=10, pady=10)
tk.Button(root, text="💾 \n Exportar CSV ", bg="#27ae60", fg="white", command=export_inventory_to_csv).pack(padx=10, pady=10)

columns = ("Código", "Producto", "Ubicación", "Precio", "Cantidad", "Total")

table = ttk.Treeview(root, columns=columns, show="headings")
scrollbar = ttk.Scrollbar(root, orient="vertical", command=table.yview)
table.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")
table.pack(fill="both", expand=True)

# Configuramos los títulos (HEADERS)
for col in columns:
    # Agregamos el comando de ordenamiento al encabezado
    table.heading(col, text=col, command=lambda _col=col: sort_column(table, _col, False))
    table.column(col, width=100, anchor="center")

table.column("Precio", anchor="e", width=100)
table.column("Cantidad", anchor="e", width=80)
table.column("Total", anchor="e", width=120)

for col in columns:
    table.heading(col, text=col)

cargar()
root.mainloop()