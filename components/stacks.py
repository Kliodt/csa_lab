class DataStack:
    stack: list[int]
    _top: int
    stack_size: int

    def __init__(self, stack_size):
        self.stack = [0] * stack_size
        self._top = 0
        self.stack_size = stack_size

    def push(self, value: int):
        assert self._top < self.stack_size, "data stack overflow"
        self.stack[self._top] = value
        self._top += 1

    def pop(self) -> int:
        assert self._top >= 1, "data stack underflow"
        self._top -= 1
        return self.stack[self._top]

    def top(self) -> int:
        assert self._top >= 1, "data stack underflow"
        return self.stack[self._top - 1]

    def dup(self):
        self.push(self.top())

    def swap(self):
        assert self._top >= 2, "data stack underflow"
        [self.stack[self._top - 1], self.stack[self._top - 2]] = [
            self.stack[self._top - 2],
            self.stack[self._top - 1],
        ]

    def __repr__(self):
        stack_repr = "["
        if 1 <= self._top:
            stack_repr += f"{str(self.stack[self._top-1])}"
        if 2 <= self._top:
            stack_repr += f", {str(self.stack[self._top - 2])}"
        if 3 <= self._top:
            stack_repr += f", {str(self.stack[self._top-3])}"
        if 4 <= self._top:
            stack_repr += f",... +{self._top - 3}"
        return stack_repr + "]"


class CallStack:
    stack: list[int]
    _top: int
    stack_size: int

    def __init__(self, stack_size):
        self.stack = [0] * stack_size
        self._top = 0
        self.stack_size = stack_size

    def push(self, value: int):
        assert self._top < self.stack_size, "call stack overflow"
        self.stack[self._top] = value
        self._top += 1

    def pop(self) -> int:
        assert self._top >= 1, "call stack underflow"
        self._top -= 1
        return self.stack[self._top]
