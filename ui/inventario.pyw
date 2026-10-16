import tkinter as tk
from tkinter import ttk, messagebox
from services import inventario_service as service
from utils.window_manager import *

def load_inventory():
    table.delete(*table.get_children())
    for row in service.fetch_inventory():
        table.insert("", tk.END, values=row)

def add_product():
    try:
        service.add_product(
            entry_cod.get(),
            entry_prod.get(),
            entry_ubic.get(),
            float(entry_precio.get()),
            int(entry_cant.get())
        )
        load_inventory()
        clear_fields()
    except:
        messagebox.showerror("Error", "Datos inválidos")

def update_product():
    selected = table.selection()
    if not selected:
        messagebox.showwarning("Advertencia", "Seleccione un producto")
        return

    cod = table.item(selected[0])["values"][0]

    try:
        service.update_product(
            cod,
            entry_prod.get(),
            entry_ubic.get(),
            float(entry_precio.get()),
            int(entry_cant.get())
        )
        load_inventory()
        clear_fields()
    except:
        messagebox.showerror("Error", "Datos inválidos")

def delete_product():
    selected = table.selection()
    if not selected:
        messagebox.showwarning("Advertencia", "Seleccione un producto para eliminar.")
        return

    # Obtenemos el código de la primera columna
    cod = table.item(selected[0])["values"][0]

    confirm = messagebox.askyesno("Confirmar", f"¿Eliminar el producto con código {cod}?")
    if confirm:
        # GUARDAMOS EL RESULTADO EN UNA VARIABLE
        exito = service.delete_product_db(cod)
        
        if exito:
            messagebox.showinfo("Éxito", "Producto eliminado correctamente.")
            load_inventory()
            clear_fields()
        else:
            messagebox.showerror("Error", "No se pudo eliminar el producto de la base de datos.")

def load_product_data(event):
    selected = table.selection()
    if selected:
        values = table.item(selected[0])["values"]

        entry_cod.config(state='normal')
        entry_cod.delete(0, tk.END)
        entry_cod.insert(0, values[0])
        entry_cod.config(state='readonly')

        entry_prod.delete(0, tk.END)
        entry_prod.insert(0, values[1])

        entry_ubic.delete(0, tk.END)
        entry_ubic.insert(0, values[2])

        entry_precio.delete(0, tk.END)
        entry_precio.insert(0, values[3])

        entry_cant.delete(0, tk.END)
        entry_cant.insert(0, values[4])

def clear_fields():
    search_entry.delete(0, tk.END)
    entry_cod.config(state='normal')
    entry_cod.delete(0, tk.END)
    entry_prod.delete(0, tk.END)
    entry_ubic.delete(0, tk.END)
    entry_precio.delete(0, tk.END)
    entry_cant.delete(0, tk.END)

def search_inventory(event=None):
    term = search_entry.get().strip()

    table.delete(*table.get_children())

    if not term:
        load_inventory()
        return

    for row in service.search_inventory(term):
        table.insert("", tk.END, values=row)

# UI
root = tk.Tk()
root.title("📊 Inventario")
center_window(root, 900, 400)
root.config(bg="#2c3e50")

search_entry = tk.Entry(root, width=50)
search_entry.pack(padx=10, pady=10)

search_entry.bind("<Return>", search_inventory)

tk.Button(root, text="Buscar", command=search_inventory, bg="#27ae60", fg="white").pack()

frame_formulario = tk.Frame(root, padx=20, pady=20)
frame_formulario.pack(side="left", fill="y", anchor="n")
frame_formulario.config(bg="#2c3e50")

# --- SECCIÓN DE ENTRADAS (LABELS + ENTRIES) ---
# Usamos grid dentro del frame para que queden en columnas
labels = ["Código:", "Producto:", "Ubicación:", "Precio:", "Cantidad:"]
entries = []

for i, text in enumerate(labels):
    tk.Label(frame_formulario, text=text, bg="#2c3e50", fg="white").grid(row=i, column=0, sticky="w", pady=5)
    
entry_cod = tk.Entry(frame_formulario)
entry_cod.grid(row=0, column=1, pady=5, padx=5)

entry_prod = tk.Entry(frame_formulario)
entry_prod.grid(row=1, column=1, pady=5, padx=5)

entry_ubic = tk.Entry(frame_formulario)
entry_ubic.grid(row=2, column=1, pady=5, padx=5)

entry_precio = tk.Entry(frame_formulario)
entry_precio.grid(row=3, column=1, pady=5, padx=5)

entry_cant = tk.Entry(frame_formulario)
entry_cant.grid(row=4, column=1, pady=5, padx=5)

# --- SECCIÓN DE BOTONES ---
# Creamos un sub-frame para los botones dentro del formulario
frame_botones = tk.Frame(frame_formulario, pady=20)
frame_botones.grid(row=5, column=0, columnspan=2)
frame_botones.config(bg="#2c3e50")

# Botones organizados en una pequeña cuadrícula
tk.Button(frame_botones, text="Agregar", bg="#27ae60", fg="white", command=add_product, width=15).grid(row=0, column=0, padx=2, pady=2)
tk.Button(frame_botones, text="Actualizar", bg="#27ae60", fg="white", command=update_product, width=15).grid(row=0, column=1, padx=2, pady=2)
tk.Button(frame_botones, text="Limpiar", bg="#27ae60", fg="white", command=clear_fields, width=15).grid(row=1, column=0, padx=2, pady=2)
tk.Button(frame_botones, text="Eliminar", bg="#27ae60", fg="white", command=delete_product, width=15).grid(row=1, column=1, padx=2, pady=2)
tk.Button(frame_botones, text="Reporte Inventario", bg="#27ae60", fg="white", command=lambda: abrir_ventana(root, "ui/reporte_inv.pyw"), width=32).grid(row=2, column=0, columnspan=2, padx=2, pady=10)

columns = ("Código", "Producto", "Ubicación", "Precio", "Cantidad", "Total")

# 1. Definimos la tabla y sus columnas
table = ttk.Treeview(root, columns=columns, show="headings")

# scrollbar
scrollbar = ttk.Scrollbar(root, orient="vertical", command=table.yview)
table.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")

# Configuramos los títulos (HEADERS)
for col in columns:
    # Agregamos el comando de ordenamiento al encabezado
    table.heading(col, text=col, command=lambda _col=col: sort_column(table, _col, False))
    table.column(col, width=100, anchor="center")

# Columnas de Texto (Alineadas a la izquierda: 'w' de West)
table.column("Código", anchor="w", width=100)
table.column("Producto", anchor="w", width=200)
table.column("Ubicación", anchor="w", width=150)

# Columnas Numéricas (Alineadas a la derecha: 'e' de East)
table.column("Precio", anchor="e", width=100)
table.column("Cantidad", anchor="e", width=80)
table.column("Total", anchor="e", width=120)

table.pack(padx=10, pady=10, expand=True, fill='both')
table.bind("<<TreeviewSelect>>", load_product_data)

load_inventory()
root.mainloop()