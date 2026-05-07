class HashMap:
    hashmap: list[tuple[str, str] | None]

    def insert(self, key, value):
        self.resize()
        index = self.key_to_index(key)
        original_index = index
        first_iteration = True
        while (slot := self.hashmap[index]) is not None and slot[0] != key:
            if not first_iteration and index == original_index:
                raise Exception("hashmap is full")
            index += 1
            index = index % len(self.hashmap)
            first_iteration = False
        self.hashmap[index] = (key, value)

    def get(self, key):
        index = self.key_to_index(key)
        original_index = index
        first_iteration = True
        while (slot := self.hashmap[index]) is not None:
            if slot[0] == key:
                return slot[1]
            if not first_iteration and index == original_index:
                raise Exception("hashmap is full")
            index += 1
            index = index % len(self.hashmap)
            first_iteration = False
        raise Exception("sorry, key not found")

    def resize(self):
        if len(self.hashmap) == 0:
            self.hashmap = [None]
            return
        load = self.current_load()
        if load >= 0.7:
            old_entries = [pair for pair in self.hashmap if pair is not None]
            self.hashmap = [None] * (2 * len(self.hashmap))
            for key, value in old_entries:
                self.insert(key, value)

    def current_load(self):
        if len(self.hashmap) == 0:
            return 1
        filled = 0
        for pair in self.hashmap:
            if pair is not None:
                filled += 1
        return filled / len(self.hashmap)

    # don't touch below this line

    def __init__(self, size):
        self.hashmap = [None for i in range(size)]

    def key_to_index(self, key):
        total = 0
        for c in key:
            total += ord(c)
        return total % len(self.hashmap)

    def __repr__(self):
        final = ""
        for i, v in enumerate(self.hashmap):
            if v != None:
                final += f" - {str(v)}\n"
        return final
