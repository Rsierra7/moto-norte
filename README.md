# Moto Norte

Aplicación de escritorio en Python para la gestión de un taller de motos.

## Funcionalidades

- Gestión de inventario.
- Registro de ventas.
- Generación de facturas.
- Reportes de inventario y ventas.

## Tecnologías

- Python y Tkinter.
- MySQL.
- MySQL Connector/Python.
- python-dotenv.
- tkcalendar.
- pywin32 para impresión en Windows.

## Requisitos

- Windows.
- Python 3.13 con Tkinter.
- Servidor MySQL y MySQL Workbench.
- Git o GitHub Desktop con acceso al repositorio.

La aplicación se ha ejecutado con Python 3.13 y MySQL 9.3.
Los archivos SQL utilizan la intercalación utf8mb4_0900_ai_ci.

## Instalación

### 1. Obtener el proyecto

Clonar el repositorio con GitHub Desktop o ejecutar:

```powershell
git clone https://github.com/Rsierra7/moto-norte.git
cd moto-norte
git switch develop
```

### 2. Crear un entorno virtual

Desde la carpeta principal del proyecto:

```powershell
py -3.13 -m venv .venv
```

Instalar las dependencias usando el Python del entorno:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

No es necesario activar el entorno para usar estos comandos.

### 3. Preparar una base de datos vacía

Los siguientes pasos son para una instalación nueva.

**Los archivos SQL incluyen DROP TABLE. No deben ejecutarse sobre
una base de datos con información que se quiera conservar.**

En MySQL Workbench, ejecutar:

```sql
CREATE DATABASE motonorte
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;
```

Actualizar el panel Schemas y seleccionar motonorte como esquema
predeterminado mediante doble clic.

Abrir los archivos de la carpeta database con File → Open SQL Script.
Antes de ejecutar cada archivo, comprobar que motonorte sea el esquema
predeterminado.

Ejecutarlos individualmente en este orden:

1. database/motonorte_inventario.sql
2. database/motonorte_proveedores.sql
3. database/motonorte_compras.sql
4. database/motonorte_ventas.sql

La tabla ventas depende de inventario mediante una clave foránea.

Estos archivos contienen únicamente la estructura. No incluyen productos,
proveedores, compras ni ventas de ejemplo.

### 4. Configurar la conexión

Desde la carpeta principal:

```powershell
Copy-Item .env.example .env
```

Editar el archivo .env con los datos de conexión locales:

```dotenv
DB_HOST=localhost
DB_USER=tu_usuario
DB_PASSWORD="tu_contraseña"
DB_NAME=motonorte
```

El usuario de MySQL debe tener permisos sobre la base de datos.

El archivo .env no se incluye en Git. Al clonar el proyecto en otro
equipo, debe configurarse nuevamente.

## Ejecución

Desde la carpeta principal:

```powershell
.\.venv\Scripts\python.exe main.pyw
```

## Comprobación inicial

- Abrir Inventario.
- Abrir Ventas.
- Abrir Reporte Ventas.
- Verificar que no aparezcan errores de conexión o importación.

En una instalación nueva, las tablas estarán vacías.
La impresión requiere una impresora configurada en Windows.

## Estructura del proyecto

- main.pyw: ventana principal.
- db.py: conexión a MySQL y lectura del archivo .env.
- ui/: ventanas de la aplicación.
- services/: operaciones de inventario, ventas y reportes.
- utils/: utilidades compartidas y apertura de ventanas.
- database/: estructura SQL de las tablas.
- requirements.txt: dependencias de Python.
- .env.example: ejemplo de configuración sin credenciales reales.

## Archivos excluidos de Git

- Credenciales del archivo .env.
- Entornos virtuales.
- Caché de Python.
- Facturas generadas.
- Carpetas build y dist.

## Flujo de trabajo

- main: rama principal.
- develop: integración de mejoras.
- Cada cambio se realiza en una rama propia y se integra en develop
  mediante un pull request.

## Estado

## Estado

Proyecto en desarrollo.

Verificaciones realizadas en Windows con Python 3.13 y MySQL 9.3:

- Instalación de dependencias en un entorno virtual nuevo.
- Importación de los cuatro archivos SQL en una base vacía.
- Apertura de Inventario, Ventas y Reporte Ventas con la base vacía.
- Apertura de las mismas ventanas con datos existentes.

Pendiente: verificar el registro de ventas, la actualización del
inventario y la generación e impresión de facturas.