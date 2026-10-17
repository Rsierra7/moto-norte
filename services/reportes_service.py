import csv
from tkinter import messagebox, filedialog
from services.database_support import read_cursor


def get_sales_by_date(start, end):
    with read_cursor() as cursor:
        cursor.execute(
            """SELECT num_factura, fecha_venta, producto, cantidad,
            precio_unitario, total, tipo_pago FROM ventas
            WHERE DATE(fecha_venta) BETWEEN %s AND %s ORDER BY fecha_venta""",
            (start, end),
        )
        return cursor.fetchall()


def export_to_csv(suggested_name, headers, data):
    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        initialfile=suggested_name,
        filetypes=[("CSV files", "*.csv")]
    )

    if not file_path:
        return False

    try:
        with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(data)
        
        messagebox.showinfo("Éxito", "Reporte exportado correctamente")
        return True
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo exportar: {str(e)}")
        return False