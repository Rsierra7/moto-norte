import subprocess
import sys
import os

def abrir_ventana(root, script_path):
    """
    Abre un subproceso ocultando la ventana actual
    y la vuelve a mostrar cuando se cierra.
    """

    base_path = os.path.dirname(os.path.abspath(__file__))
    # subir un nivel (porque estás en /utils)
    base_path = os.path.dirname(base_path)

    ruta = os.path.join(base_path, script_path)

    root.withdraw()

    proceso = subprocess.Popen([sys.executable, ruta])
    proceso.wait()

    root.deiconify()

def sort_column(treeview, col, reverse):
    # 1. Extraer los datos de la columna junto con el ID de la fila
    # .set(item, col) obtiene el valor de la celda
    data = [(treeview.set(item, col), item) for item in treeview.get_children('')]

    # 2. Intentar convertir a número para que el orden sea lógico (ej: 10 < 100)
    # Si falla (porque es texto como el Código), lo deja como string
    try:
        data.sort(key=lambda x: float(x[0]), reverse=reverse)
    except ValueError:
        data.sort(reverse=reverse)

    # 3. Reorganizar las filas en la interfaz según el nuevo orden
    for index, (val, item) in enumerate(data):
        treeview.move(item, '', index)

    # 4. Cambiar el comando del encabezado para que el próximo clic sea el inverso
    treeview.heading(col, command=lambda: sort_column(treeview, col, not reverse))

def center_window(window, width, height):
    # 1. Obtener las dimensiones de la pantalla del usuario
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # 2. Calcular las coordenadas X e Y para el centro
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2) - 50  

    # 3. Aplicar la geometría: "Ancho x Alto + X + Y"
    window.geometry(f'{width}x{height}+{x}+{y}')