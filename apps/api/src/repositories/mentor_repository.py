from typing import Any
from google.cloud.firestore_v1.base_query import FieldFilter
from src.repositories.base import FirestoreRepository

class MentorRepository(FirestoreRepository):
    def where(self, filters: dict[str, Any] | None = None) -> list[dict]:
        query = self._collection()
        for field, value in (filters or {}).items():
            query = query.where(filter=FieldFilter(field, "==", value))

        rows = []
        for snapshot in query.stream():
            row = snapshot.to_dict() or {}
            row["id"] = snapshot.id
            rows.append(row)
        return rows
