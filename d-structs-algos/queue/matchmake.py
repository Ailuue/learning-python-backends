from custom_queue import Queue


def matchmake(queue: Queue, user: tuple[str, str]) -> str:
    name = user[0]
    action = user[1]
    if action == "leave":
        queue.search_and_remove(name)
    if action == "join":
        queue.push(name)
    if queue.size() >= 4:
        user1 = queue.pop()
        user2 = queue.pop()
        return f"{user1} matched {user2}!"
    else:
        return "No match found"