from flask import request
from pydantic import BaseModel, ValidationError
from src.core.errors import ApiError

def _translate(error: dict) -> str:
    kind = error.get("type", "")
    ctx = error.get("ctx") or {}
    if kind == "missing":
        return "es obligatorio"
    if kind == "extra_forbidden":
        return "campo no permitido"
    if kind == "string_too_short":
        return f"debe tener al menos {ctx.get('min_length')} caracteres"
    if kind == "string_too_long":
        return f"debe tener máximo {ctx.get('max_length')} caracteres"
    if kind == "too_short":
        return f"debe tener al menos {ctx.get('min_length')} elemento(s)"
    if kind == "too_long":
        return f"debe tener máximo {ctx.get('max_length')} elemento(s)"
    if kind == "greater_than_equal":
        return f"debe ser mayor o igual a {ctx.get('ge')}"
    if kind == "less_than_equal":
        return f"debe ser menor o igual a {ctx.get('le')}"
    if kind == "string_pattern_mismatch":
        return "tiene un formato inválido"
    if kind == "literal_error":
        return f"valor no permitido (opciones: {ctx.get('expected')})"
    if kind == "value_error":
        return str(ctx.get("error", error.get("msg", "valor inválido")))
    if kind.endswith("_type") or kind.endswith("_parsing"):
        return "tiene un tipo de dato inválido"
    return error.get("msg", "valor inválido")

def parse_body(schema: type[BaseModel]) -> BaseModel:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError("El cuerpo de la petición debe ser un objeto JSON", 422, "VALIDATION_ERROR")
    try:
        return schema.model_validate(data)
    except ValidationError as error:
        fields = [
            {"field": ".".join(str(p) for p in item.get("loc", ())) or "cuerpo", "message": _translate(item)}
            for item in error.errors()
        ]
        message = "; ".join(f"{f['field']}: {f['message']}" for f in fields)
        raise ApiError(message, 422, "VALIDATION_ERROR", {"fields": fields}) from error
