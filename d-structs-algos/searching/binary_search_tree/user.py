import random


class User:
    def __init__(self, id: int):
        self.id = id
        user_names = [
            "Blake",
            "Ricky",
            "Shelley",
            "Dave",
            "George",
            "John",
            "James",
            "Mitch",
            "Williamson",
            "Burry",
            "Vennett",
            "Shipley",
            "Geller",
            "Rickert",
            "Carrell",
            "Baum",
            "Brownfield",
            "Lippmann",
            "Moses",
        ]
        self.user_name = f"{user_names[id % len(user_names)]}#{id}"

    def __eq__(self, other: object)-> bool:
        return isinstance(other, User) and self.id == other.id

    def __lt__(self, other: object)-> bool:
        return isinstance(other, User) and self.id < other.id

    def __gt__(self, other: object)-> bool:
        return isinstance(other, User) and self.id > other.id

    def __repr__(self)-> str:
        return "".join(self.user_name)


def get_users(num: int) -> list[User]:
    random.seed(1)
    users = []
    ids = []
    for i in range(num * 3):
        ids.append(i)
    random.shuffle(ids)
    ids = ids[:num]
    for id in ids:
        user = User(id)
        users.append(user)
    return users
