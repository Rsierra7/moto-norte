"""Diálogos de la aplicación con textos y validación en español."""
import tkinter as tk
from tkinter import ttk
from tkinter.simpledialog import Dialog
from pathlib import Path


def parse_integer(value, minimum=None, maximum=None):
    try:
        number = int(value.strip())
    except (ValueError, AttributeError):
        raise ValueError("Ingrese un número entero válido, sin letras ni decimales.") from None
    if minimum is not None and number < minimum:
        raise ValueError(f"El valor mínimo permitido es {minimum}.")
    if maximum is not None and number > maximum:
        raise ValueError(f"El valor máximo permitido es {maximum}.")
    return number


class _Dialog(Dialog):
    def __init__(self, parent, title, message, confirm=False, query=False,
                 initialvalue="", integer=False, minvalue=None, maxvalue=None):
        self.message = message
        self.confirm = confirm
        self.query = query
        self.initialvalue = initialvalue
        self.integer = integer
        self.minimum = minvalue
        self.maximum = maxvalue
        super().__init__(parent, title)

    def body(self, master):
        ttk.Label(master, text=self.message, wraplength=480, justify="left").pack(padx=12, pady=12)
        if self.query:
            self.entry = ttk.Entry(master, width=45)
            self.entry.pack(padx=12, pady=5, fill="x")
            self.entry.insert(0, str(self.initialvalue))
            self.entry.selection_range(0, tk.END)
            return self.entry

    def buttonbox(self):
        box = ttk.Frame(self)
        box.pack(pady=12)
        yes = ttk.Button(box, text="Sí" if self.confirm else "Aceptar", command=self.ok)
        yes.pack(side="left", padx=8)
        if self.confirm or self.query:
            ttk.Button(box, text="No" if self.confirm else "Cancelar", command=self.cancel).pack(side="left", padx=8)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        if not self.query:
            yes.focus_set()

    def validate(self):
        if self.query and self.integer:
            try:
                self.number = parse_integer(self.entry.get(), self.minimum, self.maximum)
            except ValueError as exc:
                showwarning("Cantidad inválida", str(exc), parent=self)
                self.entry.selection_range(0, tk.END)
                return False
        return True

    def apply(self):
        self.result = (self.number if self.integer else self.entry.get()) if self.query else True


def _open(title, message, parent=None, **kwargs):
    parent = parent or tk._default_root
    temporary = parent is None
    if temporary:
        parent = tk.Tk()
        parent.withdraw()
    try:
        return _Dialog(parent, title, message, **kwargs).result
    finally:
        if temporary:
            parent.destroy()


def showinfo(title, message, parent=None):
    return _open(title, message, parent)


def showwarning(title, message, parent=None):
    return _open(title, message, parent)


def showerror(title, message, parent=None):
    return _open(title, message, parent)


def askyesno(title, message, parent=None):
    return bool(_open(title, message, parent, confirm=True))


def askstring(title, prompt, parent=None, initialvalue=""):
    return _open(title, prompt, parent, query=True, initialvalue=initialvalue)


def askinteger(title, prompt, parent=None, initialvalue="", minvalue=None, maxvalue=None):
    return _open(title, prompt, parent, query=True, integer=True,
                 initialvalue=initialvalue, minvalue=minvalue, maxvalue=maxvalue)


class _SaveCSV(Dialog):
    """Selector propio para evitar botones nativos en otro idioma."""
    def __init__(self, parent, suggested_name):
        self.directory = Path.home()
        self.suggested_name = suggested_name
        super().__init__(parent, "Guardar reporte CSV")

    def body(self, master):
        ttk.Label(master, text="Carpeta:").pack(anchor="w")
        bar = ttk.Frame(master)
        bar.pack(fill="x")
        self.path_entry = ttk.Entry(bar, width=65)
        self.path_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(bar, text="Ir", command=self.go).pack(side="left", padx=4)
        ttk.Button(bar, text="Subir", command=self.up).pack(side="left")
        self.files = tk.Listbox(master, width=80, height=12, exportselection=False)
        self.files.pack(fill="both", expand=True, pady=8)
        self.files.bind("<Double-1>", self.select_file)
        ttk.Label(master, text="Nombre del archivo:").pack(anchor="w")
        self.name = ttk.Entry(master, width=65)
        self.name.insert(0, self.suggested_name)
        self.name.pack(fill="x")
        self.load_directory(self.directory)
        return self.name

    def buttonbox(self):
        box = ttk.Frame(self)
        box.pack(pady=10)
        ttk.Button(box, text="Guardar", command=self.ok).pack(side="left", padx=8)
        ttk.Button(box, text="Cancelar", command=self.cancel).pack(side="left", padx=8)
        self.bind("<Escape>", self.cancel)

    def load_directory(self, directory):
        try:
            entries = sorted(directory.iterdir(), key=lambda f: (not f.is_dir(), f.name.casefold()))
            entries = [f for f in entries if f.is_dir() or f.suffix.lower() == ".csv"]
        except OSError:
            showerror("Carpeta no disponible", "No se pudo abrir la carpeta. Revisa la ruta y los permisos.", parent=self)
            return
        self.directory = directory
        self.entries = entries
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, str(directory))
        self.files.delete(0, tk.END)
        for f in entries:
            self.files.insert(tk.END, ("[Carpeta] " if f.is_dir() else "") + f.name)

    def go(self):
        self.load_directory(Path(self.path_entry.get()).expanduser())

    def up(self):
        self.load_directory(self.directory.parent)

    def select_file(self, event=None):
        selected = self.files.curselection()
        if not selected:
            return
        path = self.entries[selected[0]]
        if path.is_dir():
            self.load_directory(path)
        else:
            self.name.delete(0, tk.END)
            self.name.insert(0, path.name)

    def validate(self):
        name = self.name.get().strip()
        if not name:
            showwarning("Nombre requerido", "Escribe el nombre del archivo.", parent=self)
            return False
        path = Path(name).expanduser()
        if not path.is_absolute():
            path = self.directory / path
        if path.suffix.lower() != ".csv":
            path = Path(str(path) + ".csv")
        try:
            if not path.parent.is_dir() or path.is_dir():
                showwarning("Ruta inválida", "Selecciona una carpeta existente y un nombre de archivo válido.", parent=self)
                return False
            if path.exists() and not askyesno("Reemplazar archivo", "El archivo ya existe. ¿Deseas reemplazarlo?", parent=self):
                return False
        except OSError:
            showerror("Ruta inválida", "No se pudo acceder a la ruta indicada.", parent=self)
            return False
        self.save_path = str(path)
        return True

    def apply(self):
        self.result = self.save_path


def asksavecsv(suggested_name, parent=None):
    return _SaveCSV(parent or tk._default_root, suggested_name).result
