class Memory:
    def __init__(self, array: list):
        self.memory = array
        self.memory_size = len(array)

    def signal_read(self, addr: int):
        assert (
            0 <= addr < self.memory_size
        ), f"reading from not existing address: {addr}"
        return self.memory[addr]

    def signal_write(self, addr: int, data: int):
        assert 0 <= addr < self.memory_size, f"writing to not existing address: {addr}"
        self.memory[addr] = data
