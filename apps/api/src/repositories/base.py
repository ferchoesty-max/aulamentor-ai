from datetime import datetime, timezone
from src.core.errors import ApiError
from src.firebase.client import get_db

class FirestoreRepository:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name

    def _collection(self):
        return get_db().collection(self.collection_name)

    def get(self, doc_id: str) -> dict:
        doc_ref = self._collection().document(doc_id)
        snapshot = doc_ref.get()
        if not snapshot.exists:
            raise ApiError(f'Documento no encontrado en {self.collection_name}', 404, 'NOT_FOUND')
        data = snapshot.to_dict()
        data['id'] = snapshot.id
        return data

    def find_by_id(self, doc_id: str):
        doc_ref = self._collection().document(doc_id)
        snapshot = doc_ref.get()
        if not snapshot.exists:
            return None
        data = snapshot.to_dict()
        data['id'] = snapshot.id
        return data

    def list(self, limit: int = 50) -> list:
        docs = self._collection().limit(limit).stream()
        results = []
        for doc in docs:
            item = doc.to_dict()
            item['id'] = doc.id
            results.append(item)
        return results

    def create(self, data: dict, doc_id: str = None) -> dict:
        payload = dict(data)
        if 'created_at' not in payload:
            payload['created_at'] = datetime.now(timezone.utc).isoformat()
        if doc_id:
            ref = self._collection().document(doc_id)
            ref.set(payload)
            payload['id'] = doc_id
        else:
            _, ref = self._collection().add(payload)
            payload['id'] = ref.id
        return payload

    def update(self, doc_id: str, data: dict) -> dict:
        payload = dict(data)
        payload['updated_at'] = datetime.now(timezone.utc).isoformat()
        ref = self._collection().document(doc_id)
        snapshot = ref.get()
        if not snapshot.exists:
            raise ApiError(f'Documento no encontrado en {self.collection_name}', 404, 'NOT_FOUND')
        ref.update(payload)
        updated = ref.get().to_dict()
        updated['id'] = doc_id
        return updated

    def delete(self, doc_id: str) -> bool:
        ref = self._collection().document(doc_id)
        snapshot = ref.get()
        if not snapshot.exists:
            raise ApiError(f'Documento no encontrado en {self.collection_name}', 404, 'NOT_FOUND')
        ref.delete()
        return True
