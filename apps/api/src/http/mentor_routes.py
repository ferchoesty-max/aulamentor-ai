from src.http.routes_attempts import attempts_bp
from src.http.routes_courses import courses_bp
from src.http.routes_enrollments import enrollments_bp

def register_mentor_routes(app) -> None:
    app.register_blueprint(courses_bp)
    app.register_blueprint(enrollments_bp)
    app.register_blueprint(attempts_bp)