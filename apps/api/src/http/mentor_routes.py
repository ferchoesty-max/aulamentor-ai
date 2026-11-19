from src.http.routes_courses import courses_bp

def register_mentor_routes(app) -> None:
    app.register_blueprint(courses_bp)
