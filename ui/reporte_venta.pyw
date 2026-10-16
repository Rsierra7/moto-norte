# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime

# --- IMPORTACIONES DE TUS MÓDULOS ---
from db import get_connection
from services.reportes_service import export_to_csv
from utils.window_manager import center_window

def generate_sales_report():
    """Consulta la base de datos y llena la tabla visual."""
    start_date = entry_start_date.get()
    end_date = entry_end_date.get()

    if not start_date or not end_date:
        messagebox.showwarning("Advertencia", "Por favor, seleccione ambas fechas.")
        return

    connection = get_connection()
    if not connection:
        return

    try:
        cursor = connection.cursor()
        # Query optimizada para el reporte
        query = """
            SELECT num_factura, fecha_venta, producto, cantidad, precio_unitario, total, tipo_pago
            FROM ventas
            WHERE DATE(fecha_venta) BETWEEN %s AND %s
            ORDER BY fecha_venta ASC
        """
        cursor.execute(query, (start_date, end_date))
        rows = cursor.fetchall()

        # Limpiar la tabla antes de insertar nuevos datos
        report_table.delete(*report_table.get_children())

        total_sales = 0
        for row in rows:
            # Formateamos los precios para la vista (separador de miles)
            precio_f = f"{float(row[4]):,.0f}"
            total_f = f"{float(row[5]):,.0f}"
            
            display_row = (row[0], row[1], row[2], row[3], precio_f, total_f, row[6])
            report_table.insert("", tk.END, values=display_row)
            
            total_sales += float(row[5])

        # Actualizar el label del total
        total_label.config(text=f"Total en Rango: ${total_sales:,.0f}")
        
        if not rows:
            messagebox.showinfo("Búsqueda", "No se encontraron registros en esas fechas.")

    except Exception as e:
        messagebox.showerror("Error de Consulta", f"Ocurrió un error: {e}")
    finally:
        connection.close()

def handle_export():
    """Extrae los datos de la UI y los envía al servicio de exportación."""
    data = [report_table.item(row)["values"] for row in report_table.get_children()]
    
    if not data:
        messagebox.showwarning("Exportar", "No hay datos en la tabla para exportar.")
        return

    fecha_actual = datetime.now().strftime("%d_%m_%Y")
    nombre_sugerido = f"Reporte_Ventas_MotoNorte_{fecha_actual}.csv"
    headers = ["Factura", "Fecha", "Producto", "Cant", "Precio Unit", "Total", "Tipo Pago"]
    
    # Llamamos al servicio centralizado en report_services.py
    export_to_csv(nombre_sugerido, headers, data)

# --- CONFIGURACIÓN DE LA INTERFAZ (UI) ---
root = tk.Tk()
root.title("Moto Norte - Reporte de Ventas")
# root.geometry("950x400")
center_window(root, 950, 400)
root.configure(bg="#2c3e50")

# Panel de Filtros
filter_frame = tk.LabelFrame(root, text=" Filtros por Fecha ", padx=15, pady=15, font=("Arial", 10, "bold"))
filter_frame.configure(bg="#34495e", fg="white")
filter_frame.pack(fill="x", padx=20, pady=10)

tk.Label(filter_frame, text="Desde:", fg="white", bg="#34495e").grid(row=0, column=0, padx=5)
entry_start_date = DateEntry(filter_frame, date_pattern='yyyy-MM-dd', width=12, background='darkblue', foreground='white')
entry_start_date.grid(row=0, column=1, padx=5)

tk.Label(filter_frame, text="Hasta:", fg="white", bg="#34495e").grid(row=0, column=2, padx=5)
entry_end_date = DateEntry(filter_frame, date_pattern='yyyy-MM-dd', width=12, background='darkblue', foreground='white')
entry_end_date.grid(row=0, column=3, padx=5)

btn_buscar = tk.Button(filter_frame, text="🔍 Generar Reporte", command=generate_sales_report, 
                       bg="#2c3e50", fg="white", font=("Arial", 9, "bold"), padx=15, cursor="hand2")
btn_buscar.grid(row=0, column=4, padx=30)

# Contenedor de la Tabla
table_frame = tk.Frame(root)
# table_frame.pack(fill="both", expand=True, padx=20, pady=5)
table_frame.pack(padx=20, pady=5)

columns = ("Factura", "Fecha", "Producto", "Cant", "Precio", "Total", "Pago")
report_table = ttk.Treeview(table_frame, columns=columns, show="headings")

# Estilo de las columnas
report_table.heading("Factura", text="N° Factura")
report_table.column("Factura", width=90, anchor="center")
report_table.heading("Fecha", text="Fecha")
report_table.column("Fecha", width=110, anchor="center")
report_table.heading("Producto", text="Descripción del Producto")
report_table.column("Producto", width=300, anchor="w")
report_table.heading("Cant", text="Cant.")
report_table.column("Cant", width=60, anchor="center")
report_table.heading("Precio", text="Precio Unit.")
report_table.column("Precio", width=100, anchor="e")
report_table.heading("Total", text="Subtotal")
report_table.column("Total", width=100, anchor="e")
report_table.heading("Pago", text="Método Pago")
report_table.column("Pago", width=110, anchor="center")

report_table.pack(side="left", fill="both", expand=True)

# Scrollbar vertical
scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=report_table.yview)
report_table.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")

# Pie de página (Total y Exportar)
footer = tk.Frame(root, pady=20)
footer.configure(bg="#2c3e50")
footer.pack(fill="x", padx=20)

total_label = tk.Label(footer, text="Total en Rango: $0", font=("Arial", 13, "bold"), fg="white", bg="#2c3e50")
total_label.pack(side="left")

btn_exportar = tk.Button(footer, text="📥 Exportar a CSV", command=handle_export, 
                         bg="#27ae60", fg="white", font=("Arial", 10, "bold"), padx=20, cursor="hand2")
btn_exportar.pack(side="right")

root.mainloop()



