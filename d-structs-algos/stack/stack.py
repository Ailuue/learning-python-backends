class Stack:
    def __init__(self):
        self.items = []

    def push(self, item: str):
        self.items.append(item)

    def size(self) -> int:
        return len(self.items)

    def peek(self) -> str | None:
        if len(self.items) == 0:
            return None
        return self.items[-1]

    def pop(self) -> str | None:
        if len(self.items) == 0:
            return None
        item = self.items[-1]
        del self.items[-1]
        return item