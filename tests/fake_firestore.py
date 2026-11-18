import copy
import uuid

class FakeSnapshot:
    def __init__(self, doc_id, data):
        self.id = doc_id
        self._data = data

    @property
    def exists(self):
        return self._data is not None

    def to_dict(self):
        return copy.deepcopy(self._data) if self._data is not None else None

class FakeDocumentReference:
    def __init__(self, store, doc_id):
        self._store = store
        self.id = doc_id

    def get(self):
        return FakeSnapshot(self.id, self._store.get(self.id))

    def set(self, data):
        self._store[self.id] = copy.deepcopy(data)

    def update(self, data):
        self._store[self.id].update(copy.deepcopy(data))

    def delete(self):
        self._store.pop(self.id, None)

class FakeQuery:
    def __init__(self, store, filters=None, max_rows=None):
        self._store = store
        self._filters = filters or []
        self._max_rows = max_rows

    def where(self, *args, filter=None):
        if filter is not None:
            condition = (filter.field_path, filter.op_string, filter.value)
        else:
            condition = tuple(args)
        return FakeQuery(self._store, self._filters + [condition], self._max_rows)

    def limit(self, count):
        return FakeQuery(self._store, self._filters, count)

    def stream(self):
        rows = []
        for doc_id, data in list(self._store.items()):
            if all(self._matches(data, field, op, value) for field, op, value in self._filters):
                rows.append(FakeSnapshot(doc_id, data))
        return iter(rows[: self._max_rows] if self._max_rows else rows)

    @staticmethod
    def _matches(data, field, op, value):
        if op != "==":
            raise NotImplementedError(f"Operador no soportado en el fake: {op}")
        return data.get(field) == value

class FakeCollection(FakeQuery):
    def __init__(self, store):
        super().__init__(store)

    def document(self, doc_id=None):
        return FakeDocumentReference(self._store, doc_id or uuid.uuid4().hex[:20])

    def add(self, data):
        reference = self.document()
        reference.set(data)
        return None, reference

class FakeFirestore:
    def __init__(self):
        self.data = {}

    def collection(self, name):
        return FakeCollection(self.data.setdefault(name, {}))

    def dump(self, name):
        return copy.deepcopy(self.data.get(name, {}))
