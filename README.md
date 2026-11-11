# AulaMentor AI

Plataforma educativa con algoritmo adaptativo de recomendacion orientado a evidencias para la materia de Lenguajes Modernos de Programacion (Universidad de Guanajuato, Campus Irapuato-Salamanca).

---

## 1. Problema y Justificacion

En los cursos universitarios, las evaluaciones diagnosticas tradicionales entregan un numero global que rara vez le explica al estudiante que temas puntuales domina y en cuales presenta lagunas de conocimiento. Tampoco le asignan de inmediato lecturas o ejercicios especificos calibrados segun el tipo y dificultad de los errores cometidos.

AulaMentor AI resuelve esta situacion mediante una arquitectura desacoplada donde el servidor califica los intentos, mide el dominio conceptual por unidad tematica con una formula ponderada transparente (sin depender de cajas negras ni servicios externos de pago) y genera actividades de refuerzo con una explicacion fundamentada para cada estudiante.

---

## 2. Objetivo General y Alcance del MVP

Disenar, construir y desplegar un sistema web completo compuesto por una API REST en Python y un cliente SPA en Nuxt 4, integrados con Firebase Cloud Firestore y Firebase Authentication, cumpliendo con las tres revisiones academicas oficiales:

1. **Revision 1 (19 de noviembre de 2026):** Monorepo configurado, autenticacion con distincion de roles (docente y estudiante), persistencia inicial en Firestore para usuarios y cursos, diseno base navegable y endpoints de salud y sesion.
2. **Revision 2 (26 de noviembre de 2026):** Flujo completo de inscripcion, examen diagnostico en linea con resguardo de respuestas correctas en el backend, calificacion inmediata, motor de perfiles de dominio por tema y asignacion de recomendaciones adaptativas.
3. **Revision 3 (03 de diciembre de 2026):** Despliegue en la nube (Render para la API y Netlify para la aplicacion web), tablero analitico para el profesor con deteccion de temas criticos del grupo y suite con mas de diez pruebas automatizadas aprobadas.

---

## 3. Equipo de Desarrollo y Reparto de Responsabilidades

| Integrante | Usuario GitHub | Modulos a Cargo |
|---|---|---|
| **Fernando Daniel Tolentino Uribe (Daniel)** | `@ferchoesty-max` | Arquitectura monorepo, autenticacion en backend, motor del algoritmo adaptativo, perfiles de dominio, despliegue y pruebas base |
| **Maria Paula** | `@Paula743` | Endpoints de cursos y banco de preguntas, gestion de inscripciones e intentos, validaciones con Pydantic, reglas de Firestore y documentacion |
| **El Puga (Puga)** | `@Sheby400` | Frontend en Nuxt 4, diseno de pantallas para profesor y estudiante, componentes de examen interactivo, barras de dominio y tablero analitico |

---

## 4. Stack Tecnologico

- **Backend:** Python con Flask, Pydantic v2, Firebase Admin SDK, Pytest y Gunicorn.
- **Frontend:** Nuxt 4 (modo SPA), Vue 3, TypeScript, Tailwind CSS 4, DaisyUI 5, Pinia y Firebase Web SDK.
- **Persistencia y Acceso:** Firebase Cloud Firestore y Firebase Authentication.
- **Infraestructura de Despliegue:** Render (API) y Netlify (Frontend).

---

## 5. Estructura del Monorepo

```text
aulamentor-ai/
├── apps/
│   ├── web/                  # Frontend en Nuxt 4 + Tailwind CSS + Pinia
│   └── api/                  # Backend en Python + Flask + Firebase Admin
├── firebase/
│   ├── firestore.rules       # Reglas de seguridad para Firestore
│   └── firestore.indexes.json
├── docs/
│   ├── revisiones/
│   │   ├── R1.md             # Bitacora y evidencia de Revision 1
│   │   ├── R2.md             # Bitacora y evidencia de Revision 2
│   │   └── R3.md             # Bitacora y evidencia de Revision 3
│   ├── architecture.md       # Diagrama de arquitectura y componentes
│   ├── model.md              # Especificacion de las 7 colecciones
│   ├── api.md                # Catalogo de endpoints REST
│   └── manual.md             # Guia de usuario y cuentas demo
├── tests/                    # Pruebas automatizadas de integracion
├── evidencias/               # Recursos visuales de entrega
├── .env.example              # Variables de entorno modelo
├── firebase.json             # Configuracion de emuladores y reglas
├── netlify.toml              # Configuracion de publicacion en Netlify
├── render.yaml               # Configuracion de publicacion en Render
├── package.json              # Scripts raiz del monorepo
└── README.md
```

---

## 6. Instalacion y Puesta en Marcha Local

### Requisitos Previos
- Node.js version 20 o superior y npm version 10 o superior.
- Python version 3.11 o superior con pip.

### Preparacion de Variables
Crear el archivo `.env` en la raiz tomando como referencia `.env.example`:

```bash
cp .env.example .env
```

### Ejecucion del Backend
```bash
cd apps/api
pip install -r requirements.txt
python main.py
```
El servicio quedara disponible en `http://localhost:8000`. Verificacion de estado:
```bash
curl http://localhost:8000/api/v1/health
```

### Ejecucion de Pruebas Automatizadas
Desde la raiz del proyecto:
```bash
pytest apps/api/tests
```
