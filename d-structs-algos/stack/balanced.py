from stack import Stack


def is_balanced(input_str: str) -> bool:
    stack = Stack()
    for char in input_str:
        if char == "(":
            stack.push(char)
        elif char == ")":
            if stack.pop() is None:
                return False
    return stack.peek() is None
