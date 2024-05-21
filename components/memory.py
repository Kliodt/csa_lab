class Memory:
    def __init__(self, memory_size: int):
        self.memory = [0] * memory_size
        self.memory_size = memory_size

    def signal_read(self, addr: int):
        assert (
            0 <= addr < self.memory_size
        ), f"reading from not existing address: {addr}"
        return self.memory[addr]

    def signal_write(self, addr: int, data: int):
        assert 0 <= addr < self.memory_size, f"writing to not existing address: {addr}"
        self.memory[addr] = data
