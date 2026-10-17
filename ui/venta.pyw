# from sqlite3 import Date
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from services import ventas_service as service
from mysql.connector import Error
from services.database_support import database_message, SaleCommitUnknown
import os
import win32print
from textwrap import wrap
from tkcalendar import DateEntry

from utils.window_manager import center_window, sort_column


# =========================
# VARIABLES GLOBALES
# =========================
cart = []
sale_uncertain = False

# =========================
# FUNCIONES
# =========================

def search_product(event=None):
    term = entry_search.get().strip()
    if not term:
        table_products.delete(*table_products.get_children())
        return
    try:
        data = service.search_product(term)
    except Error as exc:
        messagebox.showerror("Error de base de datos", database_message(exc), parent=root)
        return
    table_products.delete(*table_products.get_children())
    if not data:
        messagebox.showinfo("Info", "No se encontraron productos", parent=root)
    for row in data:
        table_products.insert("", tk.END, values=row)

def add_to_cart(event=None):
    selected = table_products.selection()
    if not selected:
        return

    values = table_products.item(selected[0])["values"]
    code, product, price, available_quantity = values

    # Buscar si ya existe en el carrito
    for i, item in enumerate(cart):
        cart_code, _, qty, item_price, _ = item

        if cart_code == code:
            # Ya existe → pedir cantidad adicional
            new_qty = simpledialog.askinteger(
                "Cantidad",
                f"Producto ya agregado\nCantidad actual: {qty}\nAgregar cantidad?",
                minvalue=1
            )

            if new_qty is None:
                return

            total_qty = qty + new_qty

            if total_qty > int(available_quantity):
                messagebox.showwarning("Stock", "No hay suficiente inventario.")
                return

            subtotal = total_qty * float(item_price)

            # Actualizar lista
            cart[i] = (code, product, total_qty, item_price, subtotal)

            # Actualizar tabla
            item_id = table_cart.get_children()[i]
            table_cart.item(
                item_id,
                values=(
                    code,
                    product,
                    total_qty,
                    f"{float(item_price):,.0f}",
                    f"{subtotal:,.0f}"
                )
            )

            update_totals()
            return

    # Si NO existe → flujo normal
    ask_quantity_and_add_to_cart(code, product, price, available_quantity)

def remove_from_cart():
    selected = table_cart.selection()
    if not selected:
        return

    index = table_cart.index(selected[0])

    cart.pop(index)
    table_cart.delete(selected[0])

    update_totals()

def get_quantity(producto, stock_disponible):
    while True:
        qty = simpledialog.askinteger(
            "Cantidad",
            f"{producto}\nDisponible: {stock_disponible}\n\nIngrese cantidad:"
        )

        if qty is None: # Cancelar
            return None

        if qty <= 0:
            messagebox.showwarning("Cantidad inválida", "Ingrese un número mayor a 0.")
            continue

        if qty > int(stock_disponible):
            messagebox.showwarning("Stock", "No hay suficiente inventario.")
            continue

        return qty

def edit_cart_item(event=None):
    selected = table_cart.selection()
    if not selected:
        return

    index = table_cart.index(selected[0])
    code, product, old_qty, price, _ = cart[index]

    # Limpiar valores
    old_qty = int(str(old_qty).replace(",", ""))
    price = float(str(price).replace(",", ""))

    # 🔹 Obtener stock real
    try:
        resultados = service.search_product(code)
    except Error as exc:
        messagebox.showerror("Error de base de datos", database_message(exc), parent=root)
        return
    if not resultados:
        messagebox.showerror("Error", "No se encontró el producto.")
        return

    try:
        stock_real = int(resultados[0][4])
    except IndexError:
        stock_real = int(resultados[0][-1])

    # 🔹 Función para actualizar
    def update_item(new_qty, new_price):
        subtotal = new_qty * new_price

        cart[index] = (code, product, new_qty, new_price, subtotal)

        table_cart.item(selected[0], values=(
            code,
            product,
            new_qty,
            f"{new_price:,.0f}",
            f"{subtotal:,.0f}"
        ))

        update_totals()

    # 🔹 Validación numérica
    def ask_numeric(title, message, is_float=False, max_value=None, parent=None):
        while True:
            # 🔹 Forzar foco en ventana padre
            if parent:
                parent.lift()
                parent.attributes("-topmost", True)
                parent.after(100, lambda: parent.attributes("-topmost", False))

            value = simpledialog.askstring(title, message, parent=parent)

            if value is None:
                return None

            value = value.replace(",", "")

            try:
                num = float(value) if is_float else int(value)

                if max_value is not None and num > max_value:
                    messagebox.showwarning(
                        "Stock insuficiente",
                        f"No puedes ingresar más de {max_value} unidades.",
                        parent=parent
                    )
                    continue

                if num <= 0:
                    messagebox.showwarning(
                        "Valor inválido",
                        "El valor debe ser mayor que 0.",
                        parent=parent
                    )
                    continue

                return num

            except ValueError:
                messagebox.showwarning(
                    "Advertencia",
                    "Ingrese un valor numérico válido.",
                    parent=parent
                )

    # 🔹 CASO ESPECIAL
    if code == "MO01":
        new_price = ask_numeric("Precio", f"Ingrese nuevo precio para {product}:", True)
        if new_price is None:
            return

        update_item(old_qty, new_price)
        return

    # 🔹 Ventana
    win = tk.Toplevel()
    win.title("Editar producto")
    win.geometry("300x200")
    win.resizable(False, False)

    tk.Label(win, text=f"Editar: {product}", font=("Arial", 11, "bold")).pack(pady=10)
    tk.Label(win, text=f"Stock disponible: {stock_real}", fg="gray").pack()

    # 🔹 Editar cantidad
    def edit_qty():
        new_qty = ask_numeric(
            "Cantidad",
            f"Nueva cantidad para {product}:",
            max_value=stock_real,
            parent=win
        )
        if new_qty is None:
            return

        update_item(new_qty, price)
        win.destroy()

    # 🔹 Editar precio
    def edit_price():
        new_price = ask_numeric(
            "Precio",
            f"Nuevo precio para {product}:",
            is_float=True,
            parent=win
        )
        if new_price is None:
            return

        update_item(old_qty, new_price)
        win.destroy()

    # 🔹 Editar ambos
    def edit_both():
        new_qty = ask_numeric(
            "Cantidad",
            f"Nueva cantidad para {product}:",
            max_value=stock_real,
            parent=win
        )
        if new_qty is None:
            return

        new_price = ask_numeric(
            "Precio",
            f"Nuevo precio para {product}:",
            is_float=True,
            parent=win
        )
        if new_price is None:
            return

        update_item(new_qty, new_price)
        win.destroy()

    # 🔹 Botones
    tk.Button(win, text="Cantidad", width=20, command=edit_qty).pack(pady=5)
    tk.Button(win, text="Precio", width=20, command=edit_price).pack(pady=5)
    tk.Button(win, text="Cant y Precio", width=20, command=edit_both).pack(pady=5)

def ask_quantity_and_add_to_cart(code, product, price, available_quantity):
    qty = get_quantity(product, available_quantity)

    if qty is not None:
        subtotal = qty * float(price)
        cart.append((code, product, qty, float(price), subtotal))

        # Inserción inicial con la columna Total
        table_cart.insert(
            "", 
            tk.END, 
            values=(
                code, 
                product, 
                qty, 
                f"{float(price):,.0f}", 
                f"{subtotal:,.0f}" # <-- Columna Total
            )
        )
        update_totals()

def update_totals():
    total = sum(item[4] for item in cart)
    label_total.config(text=f"Total: ${total:,.0f}")

def add_labour_item():
    # 🔍 Verificar si ya existe MO01 ANTES de abrir ventana
    for i, item in enumerate(cart):
        code, _, _, _, _ = item

        if code == "MO01":
            respuesta = messagebox.askyesno(
                "Mano de Obra",
                "Ya existe Mano de Obra.\n¿Desea modificar el valor?"
            )

            if not respuesta:
                return  # ❌ NO → salir sin hacer nada

            # ✅ SÍ → abrir ventana para editar
            index_to_update = i
            break
    else:
        index_to_update = None  # no existe

    # 🪟 Crear ventana SOLO si se va a agregar o editar
    ventana = tk.Toplevel(root)
    ventana.title("🛠️")
    ventana.geometry("185x100")

    tk.Label(ventana, text="Valor Mano de Obra").pack()

    entry_price = tk.Entry(ventana)
    entry_price.pack()
    entry_price.focus()

    def confirm_labour(event=None):
        price_text = entry_price.get().strip()

        if not price_text:
            messagebox.showwarning("Error", "Ingrese un valor.")
            return

        try:
            price = float(price_text)
        except ValueError:
            messagebox.showwarning("Error", "Ingrese un número válido.")
            return

        # 🔁 Si existe → actualizar
        # En lugar de confiar ciegamente en el índice para obtener el item_id:
        if index_to_update is not None:
            cart[index_to_update] = ("MO01", "MANO DE OBRA", 1, price, price)
            
            # Es más seguro buscar el item en la tabla por su contenido o ID real
            children = table_cart.get_children()
            if index_to_update < len(children):
                item_id = children[index_to_update]
                table_cart.item(
                    item_id,
                    values=("MO01", "MANO DE OBRA", 1, f"{price:,.0f}", f"{price:,.0f}")
                )

        else:
            # ➕ Si no existe → agregar
            cart.append(("MO01", "MANO DE OBRA", 1, price, price))

            table_cart.insert(
                "", 
                tk.END, 
                values=("MO01", "MANO DE OBRA", 1, f"{price:,.0f}", f"{price:,.0f}")
            )

        update_totals()
        ventana.destroy()

    tk.Button(ventana, text="Guardar", command=confirm_labour).pack()

    entry_price.bind("<Return>", confirm_labour)

def get_next_invoice():
    return service.get_next_invoice()

def print_invoice(invoice, invoice_items):
    cuerpo = service.build_invoice_text(invoice, invoice_items)

    # 3. Envío directo a la impresora (Modo RAW)
    try:
        # IMPORTANTE: Cambia "POS-58" por el nombre exacto de tu impresora en Windows
        printer_name = "POS-58" 
        
        hPrinter = win32print.OpenPrinter(printer_name)
        try:
            hJob = win32print.StartDocPrinter(hPrinter, 1, (f"Factura_{invoice}", None, "RAW"))
            win32print.StartPagePrinter(hPrinter)
            
            # Usamos 'cp850' para que se impriman bien las tildes y la "ñ"
            win32print.WritePrinter(hPrinter, cuerpo.encode('cp850'))
            
            win32print.EndPagePrinter(hPrinter)
            win32print.EndDocPrinter(hPrinter)
            messagebox.showinfo("Éxito", "Factura enviada a la impresora")
        finally:
            win32print.ClosePrinter(hPrinter)
            
    except Exception as e:
        messagebox.showerror("Error de impresión", 
            f"No se pudo imprimir en '{printer_name}'.\nVerifica el nombre de la impresora.")

def save_invoice_txt(invoice, cuerpo_factura):
    try:
        folder = "invoices"

        # Crear carpeta si no existe (por seguridad)
        if not os.path.exists(folder):
            os.makedirs(folder)

        filename = os.path.join(folder, f"factura_{invoice}.txt")

        with open(filename, "w", encoding="utf-8") as f:
            f.write(cuerpo_factura)

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo guardar la factura:\n{e}")

def handle_register_button():
    global sale_uncertain
    if sale_uncertain:
        messagebox.showwarning(
            "Verificar venta", "Hay una venta pendiente de verificación. "
            "Revisa el reporte y el inventario antes de cerrar y volver a abrir Ventas.", parent=root)
        return
    payment_type = payment_type_cb.get()
    sale_date = entry_date.get()
    # Usar los importes originales, sin redondear los valores de la tabla visual.
    cart_items = list(cart)
    if not cart_items:
        messagebox.showwarning("Advertencia", "El carrito está vacío.", parent=root)
        return
    if not payment_type:
        messagebox.showwarning("Advertencia", "Seleccione un tipo de pago.", parent=root)
        return
    try:
        invoice = get_next_invoice()
        success, message = service.register_sale(invoice, cart_items, payment_type, sale_date)
    except SaleCommitUnknown as exc:
        sale_uncertain = True
        messagebox.showerror("Verificar venta", str(exc), parent=root)
        return
    except Error as exc:
        messagebox.showerror("Error de base de datos", database_message(exc), parent=root)
        return
    if not success:
        messagebox.showerror("Error al registrar venta", message, parent=root)
        return
    # Ya está confirmada: limpiar el carrito antes de guardar o imprimir el respaldo.
    table_cart.delete(*table_cart.get_children())
    cart.clear()
    update_totals()
    messagebox.showinfo("Éxito", message, parent=root)
    try:
        cuerpo_f = service.build_invoice_text(invoice, cart_items)
        save_invoice_txt(invoice, cuerpo_f)
        if messagebox.askyesno("Imprimir factura", f"¿Desea imprimir la factura {invoice}?", parent=root):
            print_invoice(invoice, cart_items)
    finally:
        reset_ui_and_data()
    
def reset_ui_and_data():
    # 1. Limpiar widgets
    table_cart.delete(*table_cart.get_children())
    table_products.delete(*table_products.get_children())
    entry_search.delete(0, tk.END)
    payment_type_cb.set("")
    
    # 2. Limpiar datos en memoria
    # USAMOS 'cart' PORQUE ES LA QUE REVISA 'add_labour_item'
    global cart
    cart.clear() 
    
    # 3. Actualizar etiquetas y totales
    update_totals() 
    
    # 4. Refrescar número de factura y labels
    label_total.config(text="Total: $0")
    try:
        new_invoice = get_next_invoice()
    except Error as exc:
        new_invoice = "No disponible"
        messagebox.showerror("Error de base de datos", database_message(exc), parent=root)
    # Mantengo tu formato de espacios para el diseño de la etiqueta
    label_invoice.config(
        text=f"N° Factura: {new_invoice}                                                                                          ", 
        font=("Arial", 10, "bold"), 
        bg="#2c3e50", 
        fg="white"
    )                                                                     

# =========================
# UI
# =========================
invoice = "Pendiente"

root = tk.Tk()
root.title("🧮 Ventas")
center_window(root, 1000, 600)
root.config(bg="#2c3e50")

# 🔍 búsqueda
# Crear el frame contenedor
frame_search = tk.Frame(root, bg="#2c3e50")
frame_search.pack(pady=10)

# Meter el Label dentro del frame y alinearlo a la izquierda
lbl_buscar = tk.Label(frame_search, text="Buscar Producto:", bg="#2c3e50", fg="white")
lbl_buscar.pack(side="left", padx=5)

# Meter el Entry dentro del mismo frame y alinearlo a la izquierda
entry_search = tk.Entry(frame_search, width=40)
entry_search.pack(side=tk.LEFT, padx=5)
entry_search.focus()
entry_search.bind("<Return>", search_product)

tk.Button(frame_search, text="Buscar", command=search_product, bg="#27ae60", fg="white").pack(side=tk.LEFT)



# 📦 productos
style = ttk.Style()
style.theme_use('vista') # 'alt', 'clam' o 'default' permiten personalizar mejor el grosor
style.configure("Vertical.TScrollbar", arrowsize=15) 

# Frame contenedor
frame_tabla = tk.Frame(root)
frame_tabla.pack(padx=10, pady=5)

# Tabla
table_products = ttk.Treeview(
    frame_tabla, 
    columns=("CODIGO", "PRODUCTO", "PRECIO", "STOCK"), 
    show="headings",
    height=5
)

table_products.column("CODIGO", width=100, anchor="w")
table_products.column("PRODUCTO", width=280, anchor="w")
table_products.column("PRECIO", width=100, anchor="e")     
table_products.column("STOCK", width=100, anchor="e")

# Scrollbar (ahora usará el estilo configurado automáticamente)
scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=table_products.yview)
table_products.configure(yscrollcommand=scrollbar.set)

# Empaquetado
table_products.pack(side="left", expand=True)
scrollbar.pack(side="right", fill="y")


for col in ("CODIGO", "PRODUCTO", "PRECIO", "STOCK"):
    table_products.heading(col, text=col, command=lambda _col=col: sort_column(table_products, _col, False))

table_products.bind("<Double-1>", add_to_cart)


frame_num = tk.Frame(root, bg="#2c3e50")
frame_num.pack(fill="y", padx=10, pady=5)
#frame_num.pack_propagate(False)  

label_invoice = tk.Label(frame_num, text=f"N° Factura: {invoice}                                                                                          ", font=("Arial", 10, "bold"), bg="#2c3e50", fg="white")
label_invoice.pack(side="left", padx=10)

add_to_cart_button = tk.Button(frame_num, text="Agregar", command=add_to_cart, bg="#27ae60", fg="white" )
add_to_cart_button.pack(side="right", padx=10)

# 🛒 carrito
frame_cart = tk.Frame(root)
frame_cart.pack(fill="both", padx=10, pady=5)

table_cart = ttk.Treeview(
    frame_cart,
    columns=("CODIGO", "PRODUCTO", "CANTIDAD", "PRECIO", "TOTAL"),
    show="headings",
    height=7
)
table_cart.pack(fill="both", expand=True, padx=10, pady=10)

table_cart.column("CODIGO", width=80, anchor="w", stretch=True)
table_cart.column("CANTIDAD", width=80, anchor="center", stretch=True)
table_cart.column("PRECIO", width=80, anchor="e", stretch=True)
table_cart.column("TOTAL", width=80, anchor="e", stretch=True)

scrollbar_cart = ttk.Scrollbar(frame_cart, orient="vertical", command=table_cart.yview)
table_cart.configure(yscrollcommand=scrollbar_cart.set)

table_cart.pack(side="left", fill="both", expand=True)
scrollbar_cart.pack(side="right", fill="y")

for col in ("CODIGO", "PRODUCTO", "CANTIDAD", "PRECIO", "TOTAL"):
    table_cart.heading(col, text=col, command=lambda _col=col: sort_column(table_cart, _col, False))

# double click para editar cantidad
table_cart.bind("<Double-1>", edit_cart_item)


# 🔘 botones carrito
frame_buttons = tk.Frame(root, bg="#2c3e50")
# 1. Configuración de pesos (Crucial para el centrado)
# La columna 0 y la columna 4 funcionarán como "resortes"
frame_buttons.columnconfigure(0, weight=1) # Empuja desde la izquierda
frame_buttons.columnconfigure(4, weight=1) # Empuja desde la derecha de los botones

# 2. Botones (Columnas 1, 2, 3 para que estén juntos)
tk.Button(frame_buttons, text="  Borrar todo  ", command=lambda: [cart.clear(), table_cart.delete(*table_cart.get_children()), update_totals()], bg="#27ae60", fg="white").grid(row=0, column=0, padx=20)
tk.Button(frame_buttons, text="Eliminar Item", command=remove_from_cart, bg="#27ae60", fg="white").grid(row=0, column=1, padx=10)
tk.Button(frame_buttons, text="  Editar  ", command=edit_cart_item, bg="#27ae60", fg="white").grid(row=0, column=2, padx=10)
tk.Button(frame_buttons, text="Mano de Obra", command=add_labour_item, bg="#27ae60", fg="white").grid(row=0, column=3, padx=10)


# 3. Fecha (Columnas 5 y 6)
tk.Label(frame_buttons, text="Fecha de Venta:", bg="#2c3e50", fg="white").grid(row=0, column=5, pady=10, sticky="e")
entry_date = DateEntry(frame_buttons, date_pattern="yyyy-MM-dd")
entry_date.grid(row=0, column=6, padx=5, sticky="e")

tk.Label(frame_buttons, text="Tipo de Pago:", bg="#2c3e50", fg="white").grid(row=3, column=5, padx=5, pady=5, sticky="e")
payment_type_cb = ttk.Combobox(frame_buttons, values=["Efectivo", "Nequi", "Daviplata", "T. Créd/Déb",  "Transferencia"], state="readonly")
payment_type_cb.grid(row=3, column=6, padx=5, pady=5, sticky="e")

# IMPORTANTE: El frame debe ocupar todo el ancho disponible
frame_buttons.pack(fill="x", padx=10, pady=5)
    

# 💰 total
label_total = tk.Label(root, text="Total: $0", font=("Arial", 14, "bold"), bg="#2c3e50", fg="white")
label_total.pack(pady=10)

# 🧾 acciones
frame_actions = tk.Frame(root, bg="#2c3e50")
frame_actions.pack(pady=10)

tk.Button(frame_actions, text="💾 Registrar Venta", command=handle_register_button, width=20, bg="#27ae60", fg="white").grid(row=0, column=0, padx=5)
# tk.Button(frame_actions, text="🧾 Imprimir", command=print_invoice, width=20).grid(row=0, column=1, padx=5)

def load_invoice_number():
    try:
        number = get_next_invoice()
    except Error as exc:
        label_invoice.config(text="N° Factura: No disponible")
        messagebox.showerror("Error de base de datos", database_message(exc), parent=root)
        return
    label_invoice.config(text=f"N° Factura: {number}")

root.after(0, load_invoice_number)
root.mainloop()