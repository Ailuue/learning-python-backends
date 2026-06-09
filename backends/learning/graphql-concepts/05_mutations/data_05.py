from dataclasses import dataclass


@dataclass
class TodoItem:
    id: str
    title: str
    done: bool = False
    priority: int = 1


_SEED = [
    {"id": "1", "title": "Learn GraphQL schema basics",  "done": True,  "priority": 1},
    {"id": "2", "title": "Understand relationships",      "done": True,  "priority": 1},
    {"id": "3", "title": "Implement DataLoaders",         "done": False, "priority": 2},
    {"id": "4", "title": "Practice mutations",            "done": False, "priority": 1},
]

items: list[dict] = []
_next_id: int = 5


def reset() -> None:
    global items, _next_id
    items = [r.copy() for r in _SEED]
    _next_id = 5


reset()
