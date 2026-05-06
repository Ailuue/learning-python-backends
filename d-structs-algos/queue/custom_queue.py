class Queue:
    def __init__(self):
        self.items = []

    def push(self, item: str):
        self.items.insert(0, item)

    def pop(self) -> str | None:
        if len(self.items) == 0:
            return None
        temp = self.items[-1]
        del self.items[-1]
        return temp

    def peek(self) -> str | None:
        if len(self.items) == 0:
            return None
        return self.items[-1]

    def size(self) -> int:
        return len(self.items)

    def search_and_remove(self, item: str) -> str | None:
        if item not in self.items:
            return None
        self.items.remove(item)
        return item

    def __repr__(self) -> str:
        return f"[{', '.join(self.items)}]"
