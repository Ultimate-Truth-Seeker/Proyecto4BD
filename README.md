# Proyecto 4 con Django y PostgreSQL

## Descripción
Este sistema de biblioteca fue implementado utilizando el **ORM de Django** junto con extensiones de SQL personalizadas en PostgreSQL para representar información compleja como condiciones de libros, pagos y reseñas. También se diseñaron *triggers* y *views* para mantener la integridad, automatizar procesos y facilitar consultas de reportes avanzados.


## Requisitos
- **Python** 3.x
- **Django** (>= 3.x)
- **PostgreSQL** (>= 12)
- **psycopg2-binary** (para la conexión de Django a PostgreSQL)

## Instalación
1. Clona el repositorio:
   ```bash
   git clone https://github.com/Ultimate-Truth-Seeker/Proyecto4BD.git
   cd Proyecto4BD
   ```
2. Crea y activa un entorno virtual:
   ```bash
   python -m venv env
   source env/bin/activate    # Linux/macOS
   env\Scripts\activate     # Windows
   ```
3. Instala las dependencias:
   ```bash
   pip install Django psycopg2-binary
   ```

## Configuración de la base de datos
En `settings.py`, ajusta el diccionario `DATABASES` con tus credenciales:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': '<nombre_bd>',
        'USER': '<usuario>',
        'PASSWORD': '<contraseña>',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## Migraciones y ejecución
Aplicar migraciones y levantar el servidor de desarrollo:
```bash
python manage.py migrate
python manage.py runserver
```
Accede en el navegador a 
`http://127.0.0.1:8000/catalogo/`
`http://127.0.0.1:8000/prestamos/`
`http://127.0.0.1:8000/sucursales/` 
para ver la aplicación.

## Población de datos
Para cargar datos de ejemplo, ejecuta el script SQL:
```bash
psql -U <usuario> -d <nombre_bd> -f data.sql
```

## Diagrama ERD
![Diagrama ERD](ERD.png)

## 🗂️ Estructura del Modelo ERD

El modelo relacional representa entidades clave de una biblioteca como:

- **Usuarios** (`LibraryUser`)
- **Libros y Autores** (`Book`, `Author`, `BookAuthor`, `BookGenre`)
- **Géneros literarios** (`Genre`)
- **Copias físicas** (`Copy`)
- **Préstamos y Reservas** (`Loan`, `Reservation`)
- **Multas y Pagos** (`Fine`, `Payment`, `PaymentMethod`)
- **Eventos y Asistencias** (`Event`, `EventAttendance`)
- **Opiniones y Votos** (`Review`, `ReviewVote`)
- **Sucursales y Estanterías** (`Branch`, `Shelf`)
- **Control de acceso** (`Role`, `Permission`, `RolePermission`)
- **Auditoría de cambios** (`AuditLog`)

---

## 🛠️ Extensiones de PostgreSQL

### 📘 Tipos Personalizados

```sql
CREATE TYPE book_condition AS ENUM ('new','good','fair','poor');
CREATE TYPE rating_scale AS ENUM ('poor','average','good','excellent');
CREATE TYPE money AS (amount numeric(12,2), currency char(3));
```

Estos tipos permiten enriquecer la semántica de los datos y optimizar validaciones.

---

### 🔁 Triggers y Funciones Automatizadas

- **`trg_update_copy_available`**: actualiza la disponibilidad de una copia cuando se realiza o devuelve un préstamo.
- **`trg_generate_fine`**: genera automáticamente una multa si se devuelve un libro con retraso.
- **`trg_books_audit`**: inserta registros en `AuditLog` cuando se modifica un libro.

También se implementó la función `calc_overdue_fine(p_loan)` para calcular multas basadas en los días de retraso.

---

## 👁️ Vistas de Reporte (Views)

### 1. `vista_catalogo_libros`

Proporciona una vista agregada de cada libro, con información sobre:
- Autor principal y otros autores
- Géneros asociados
- Total y disponibilidad de copias
- Reseñas y rating promedio

### 2. `vista_prestamos_usuarios`

Muestra un resumen completo de actividad por usuario:
- Número de préstamos (activos, devueltos, vencidos)
- Multas totales y pendientes
- Estado general del usuario (ej. "Con retrasos", "Con multas")

### 3. `vista_actividad_sucursales`

Reporta el nivel de actividad de cada sucursal:
- Copias disponibles vs. prestadas
- Préstamos históricos y activos
- Eventos organizados y asistencias
- Porcentaje de ocupación e indicadores como "Alta ocupación"

---

## ✅ Estado Actual

- Sistema completo funcional con relaciones bien definidas y validadas.
- Las vistas y funciones SQL están listas para uso en reportes administrativos.
- Puede ser utilizado como backend robusto para interfaces web, aplicaciones móviles o dashboards.

---

