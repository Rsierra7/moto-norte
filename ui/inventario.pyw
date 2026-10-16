import tkinter as tk
from tkinter import ttk, messagebox
from mysql.connector import Error
from db import DatabaseConnectionError
from services import inventario_service as service
from utils.window_manager import abrir_ventana, center_window, sort_column


def show_database_error(exc):
    if isinstance(exc, DatabaseConnectionError):
        message = str(exc)
    elif exc.errno == 1062:
        message = "Ya existe un producto con ese código."
    elif exc.errno in (1451, 1452):
        message = "La operación no se puede completar porque existen registros relacionados."
    else:
        message = "No se pudo completar la operación en MySQL. Revisa la conexión y la estructura de la base."
    messagebox.showerror("Error de base de datos", message, parent=root)


def replace_rows(rows):
    table.delete(*table.get_children())
    for row in rows:
        table.insert("", tk.END, values=row)


def load_inventory():
    try:
        rows = service.fetch_inventory()
    except Error as exc:
        show_database_error(exc)
        return False
    replace_rows(rows)
    return True


def refresh_after_write():
    clear_fields()
    if not load_inventory():
        messagebox.showwarning(
            "Actualizar inventario",
            "El cambio se guardó, pero no se pudo actualizar la tabla. "
            "No repitas la operación; pulsa Buscar para volver a consultar.",
            parent=root,
        )


def add_product():
    try:
        precio = float(entry_precio.get())
        cantidad = int(entry_cant.get())
    except ValueError:
        messagebox.showerror("Error", "Precio o cantidad inválidos", parent=root)
        return
    try:
        service.add_product(entry_cod.get(), entry_prod.get(), entry_ubic.get(), precio, cantidad)
    except Error as exc:
        show_database_error(exc)
        return
    refresh_after_write()


def update_product():
    selected = table.selection()
    if not selected:
        messagebox.showwarning("Advertencia", "Seleccione un producto", parent=root)
        return
    cod = table.item(selected[0])["values"][0]
    try:
        precio = float(entry_precio.get())
        cantidad = int(entry_cant.get())
    except ValueError:
        messagebox.showerror("Error", "Precio o cantidad inválidos", parent=root)
        return
    try:
        service.update_product(cod, entry_prod.get(), entry_ubic.get(), precio, cantidad)
    except Error as exc:
        show_database_error(exc)
        return
    refresh_after_write()


def delete_product():
    selected = table.selection()
    if not selected:
        messagebox.showwarning("Advertencia", "Seleccione un producto para eliminar.", parent=root)
        return
    cod = table.item(selected[0])["values"][0]
    if not messagebox.askyesno("Confirmar", f"¿Eliminar el producto con código {cod}?", parent=root):
        return
    try:
        deleted = service.delete_product_db(cod)
    except Error as exc:
        show_database_error(exc)
        return
    if deleted:
        messagebox.showinfo("Éxito", "Producto eliminado correctamente.", parent=root)
    else:
        messagebox.showwarning("Advertencia", "El producto ya no existe.", parent=root)
    refresh_after_write()


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
    if not term:
        return load_inventory()
    try:
        rows = service.search_inventory(term)
    except Error as exc:
        show_database_error(exc)
        return False
    replace_rows(rows)
    return True

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