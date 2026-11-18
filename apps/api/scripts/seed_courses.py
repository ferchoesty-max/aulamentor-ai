import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]  # apps/api
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

COURSE_ID = "seed-course-eda101"

COURSE = {
    "title": "Estructuras de Datos y Algoritmos",
    "code": "EDA-101",
    "description": "Curso ficticio para demostración: arreglos, árboles y grafos.",
    "topics": ["Arreglos y Listas", "Árboles Binarios", "Grafos y Recorridos"],
    "status": "active",
}

def _activity(topic: str, level_hint: str) -> dict:
    return {
        "title": f"Refuerzo de {topic} ({level_hint})",
        "description": f"Repasa la guía base de {topic} y resuelve 2 ejercicios guiados antes de continuar.",
    }

# (id, tema, dificultad, enunciado, opciones, índice correcto)
QUESTIONS = [
    ("seed-q-arr-1", "Arreglos y Listas", 1,
     "¿Cuál es la complejidad de acceder a un elemento de un arreglo por su índice?",
     ["O(1)", "O(n)", "O(log n)", "O(n²)"], 0),
    ("seed-q-arr-2", "Arreglos y Listas", 2,
     "¿Qué ventaja tiene una lista enlazada sobre un arreglo estático?",
     ["Acceso aleatorio en O(1)", "Inserción al inicio en O(1)", "Menor uso de memoria por elemento", "Mejor localidad de caché"], 1),
    ("seed-q-arr-3", "Arreglos y Listas", 3,
     "¿Cuál es el costo amortizado de agregar un elemento al final de un arreglo dinámico que duplica su capacidad?",
     ["O(n)", "O(log n)", "O(1)", "O(n log n)"], 2),
    ("seed-q-arb-1", "Árboles Binarios", 1,
     "En un árbol binario, ¿cuántos hijos tiene como máximo cada nodo?",
     ["1", "2", "3", "Ilimitados"], 1),
    ("seed-q-arb-2", "Árboles Binarios", 2,
     "¿Qué recorrido de un árbol binario de búsqueda visita las claves en orden ascendente?",
     ["Preorden", "Postorden", "Inorden", "Por niveles"], 2),
    ("seed-q-arb-3", "Árboles Binarios", 3,
     "¿Cuál es la altura mínima de un árbol binario con 15 nodos (la raíz tiene altura 0)?",
     ["2", "3", "4", "7"], 1),
    ("seed-q-gra-1", "Grafos y Recorridos", 1,
     "¿Qué estructura de datos usa el recorrido en anchura (BFS)?",
     ["Pila", "Cola", "Montículo", "Árbol AVL"], 1),
    ("seed-q-gra-2", "Grafos y Recorridos", 2,
     "¿Qué estructura usa de forma natural el recorrido en profundidad (DFS) iterativo?",
     ["Cola", "Cola de prioridad", "Pila", "Tabla hash"], 2),
    ("seed-q-gra-3", "Grafos y Recorridos", 3,
     "¿Qué algoritmo calcula caminos mínimos desde un origen en un grafo con pesos no negativos?",
     ["Kruskal", "Dijkstra", "Prim", "Orden topológico"], 1),
]

LEVEL_HINT = {1: "básico", 2: "intermedio", 3: "avanzado"}

def build_documents(teacher_uid: str, teacher_name: str, now=None) -> dict:
    now = now or datetime.now(timezone.utc).isoformat()
    course = {**COURSE, "teacher_uid": teacher_uid, "teacher_name": teacher_name, "created_at": now, "updated_at": now}
    questions = {}
    for question_id, topic, difficulty, statement, options, correct_index in QUESTIONS:
        questions[question_id] = {
            "course_id": COURSE_ID,
            "topic": topic,
            "difficulty": difficulty,
            "statement": statement,
            "options": options,
            "correct_index": correct_index,
            "reinforcement_activity": _activity(topic, LEVEL_HINT[difficulty]),
            "active": True,
            "created_by": teacher_uid,
            "created_at": now,
            "updated_at": now,
        }
    return {"courses": {COURSE_ID: course}, "questions": questions}

def seed(db, teacher_uid: str, teacher_name: str) -> dict:
    documents = build_documents(teacher_uid, teacher_name)
    for collection, rows in documents.items():
        for document_id, data in rows.items():
            db.collection(collection).document(document_id).set(data)
    return {collection: len(rows) for collection, rows in documents.items()}

def find_teacher(teacher_uid: str | None, teacher_email: str, teacher_name: str):
    if teacher_uid:
        return teacher_uid, teacher_name

    from src.services.repos import users_repo

    matches = users_repo.where({"email": teacher_email})
    if not matches:
        sys.exit(f"No hay un usuario con correo {teacher_email} en users. Inicia sesión una vez con esa cuenta o usa --teacher-uid.")
    return matches[0]["id"], matches[0].get("display_name", teacher_name)

def main() -> None:
    parser = argparse.ArgumentParser(description="Carga datos semilla ficticios de AulaMentor AI")
    parser.add_argument("--teacher-uid", default=None, help="UID del docente dueño del curso")
    parser.add_argument("--teacher-name", default="Docente Demo")
    parser.add_argument("--teacher-email", default="docente@aulamentor.test")
    args = parser.parse_args()

    import src.config
    from src.firebase.client import get_db

    uid, name = find_teacher(args.teacher_uid, args.teacher_email, args.teacher_name)
    counts = seed(get_db(), uid, name)
    print(f"Semilla lista para el docente {name} ({uid}): {counts}")

if __name__ == "__main__":
    main()
