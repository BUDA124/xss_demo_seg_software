# Demo de Stored XSS (Seguridad en Software)

Este repositorio contiene una aplicación web deliberadamente vulnerable desarrollada en Flask para demostrar el funcionamiento, impacto y mitigación de una vulnerabilidad de **Stored Cross-Site Scripting (XSS Almacenado)**.

---

## Estructura del Proyecto

```text
xss_demo_seg_software/
├── flaskapi.py          # Backend en Flask con autenticación y rutas vulnerables
├── requirements.txt     # Dependencias de Python
├── storedxssnotes.txt   # Notas técnicas y escenarios de explotación XSS
├── templates/
│   ├── login.html       # Formulario de inicio de sesión
│   ├── home.html        # Página principal (perfil y saldo de usuario)
│   ├── comments.html    # Sección de comentarios (punto vulnerable a Stored XSS)
│   └── search.html      # Demostración secundaria de búsqueda
└── README.md            # Guía de uso y demostración
```

---

## Requisitos y Configuración

### 1. Clonar el repositorio y preparar el entorno

```bash
git clone https://github.com/BUDA124/xss_demo_seg_software.git
cd xss_demo_seg_software
```

### 2. Crear un entorno virtual (opcional pero recomendado)

```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Iniciar la aplicación

```bash
python flaskapi.py
```

La aplicación quedará disponible en: `http://localhost:5000`

---

## Usuarios de Prueba

El sistema cuenta con dos cuentas preconfiguradas en memoria:

| Usuario | Contraseña | Rol / Propósito | Saldo |
| :--- | :--- | :--- | :--- |
| `abc` | `123` | Atacante | \$50,000 |
| `def` | `456` | Víctima | \$10,000 |

---

## Guía Paso a Paso para Demostrar el Stored XSS

El **XSS Almacenado** ocurre cuando una aplicación recibe datos no confiables de un usuario, los almacena en su base de datos o memoria sin sanitizarlos, y posteriormente los muestra a otros usuarios sin escapar el contenido HTML.

### Paso 1: Iniciar sesión como atacante
1. Abre tu navegador y dirígete a `http://localhost:5000/login`.
2. Ingresa con las credenciales del atacante:
   - **Usuario**: `abc`
   - **Contraseña**: `123`
3. Serás redirigido a `/home`, donde verás tu bienvenida y saldo.

### Paso 2: Inyectar el payload en los comentarios
1. Haz clic en el enlace **"Go to Comments (Stored XSS)"** (`http://localhost:5000/comments`).
2. En el área de texto de comentarios, escribe un payload malicioso. Por ejemplo:
   ```html
   <script>alert('Stored XSS ejecutado! Cookie de sesión: ' + document.cookie);</script>
   ```
3. Presiona el botón **Post Comment**.
4. Inmediatamente el comentario se procesa y verás la alerta emergente ejecutándose en tu propio navegador.

### Paso 3: Demostrar el impacto en una víctima
1. Abre una **nueva ventana de navegación en modo incógnito** (o un navegador web diferente).
2. Entra a `http://localhost:5000/login`.
3. Inicia sesión como la víctima:
   - **Usuario**: `def`
   - **Contraseña**: `456`
4. Navega a la sección de comentarios: haz clic en **"Go to Comments (Stored XSS)"**.
5. **Resultado**: Tan pronto la página carga, el script inyectado por el usuario `abc` se ejecuta en la sesión del usuario `def`, mostrando la alerta y exponiendo la cookie de sesión de la víctima.

---

## Payloads Adicionales para la Demostración

En el archivo `storedxssnotes.txt` se detallan varios escenarios de ataque reales. Algunos ejemplos prácticos para probar en el formulario:

### A. Robo / Exfiltración de Sesión
```html
<script>
  console.log("Cookie de la víctima:", document.cookie);
</script>
```

### B. Defacement (Modificación visual del sitio)
```html
<script>
  document.querySelector("h2").innerText = "⚠️ Sitio intervenido por XSS";
  document.body.style.backgroundColor = "#ffebee";
</script>
```

### C. Phishing dentro de la aplicación
```html
<h3>Su sesión ha caducado por seguridad. Inicie sesión nuevamente:</h3>
<form action="http://localhost:5000/login" method="POST">
  <input type="text" name="username" placeholder="Usuario"><br><br>
  <input type="password" name="password" placeholder="Contraseña"><br><br>
  <button type="submit">Iniciar Sesión</button>
</form>
```

---

## Análisis Técnico de la Vulnerabilidad

### 1. Ausencia de escape en la plantilla (`templates/comments.html`)
En la plantilla se utiliza la bandera `safe` de Jinja2:
```jinja2
{% for c in comments %}
    <p>{{ c|safe }}</p>
    <hr>
{% endfor %}
```
El filtro `|safe` desactiva deliberadamente la protección por defecto de Jinja2, haciendo que el navegador interprete las etiquetas HTML y scripts directamente en lugar de tratarlos como texto plano.

### 2. Cookie de sesión sin flag `HttpOnly` (`flaskapi.py`)
```python
app.config["SESSION_COOKIE_HTTPONLY"] = False
```
Al deshabilitar `HttpOnly`, las cookies de sesión son accesibles vía JavaScript (`document.cookie`), facilitando el secuestro de sesión (Session Hijacking).

---

## Mitigación y Corrección

1. **Escapado contextual automático**: Eliminar el filtro `|safe` en Jinja2. Al renderizar `{{ c }}`, Flask y Jinja2 escapan caracteres especiales como `<`, `>`, `&`, `"`, `'` convirtiéndolos en entidades HTML (`&lt;`, `&gt;`, etc.).
2. **Protección de cookies**: Mantener `SESSION_COOKIE_HTTPONLY = True` (activado por defecto en Flask) para impedir que scripts maliciosos lean tokens de sesión.
3. **Content Security Policy (CSP)**: Habilitar cabeceras HTTP que restrinjan el origen de ejecución de scripts:
   ```python
   @app.after_request
   def set_csp(response):
       response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'"
       return response
   ```
4. **Sanitización en el servidor**: Si se requiere permitir texto enriquecido (HTML), emplear librerías de sanitización con listas blancas estrictas (como `bleach.clean(...)`).
