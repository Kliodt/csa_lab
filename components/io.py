from abc import ABC, abstractmethod


class IO(ABC):
    @abstractmethod
    def signal_in(self) -> int:
        pass

    @abstractmethod
    def signal_out(self, data: int):
        pass


class IOController:
    def __init__(self):
        self.io_list: dict[int:IO] = {}
        self.port = 0

    def add_io(self, io: IO, port: int):
        self.io_list.update({port: io})

    def remove_io(self, port: int):
        self.io_list.pop(port)

    def signal_read(self):
        assert self.port in self.io_list, f"no such i/o device: {self.port}"
        return self.io_list.get(self.port).signal_in()

    def signal_write(self, data: int):
        assert self.port in self.io_list, f"no such i/o device: {self.port}"
        self.io_list.get(self.port).signal_out(data)

    def set_port(self, port: int):
        self.port = port


# i/o devices
class IO1(IO):
    def __init__(self, data_in: list):
        self.data_in = data_in
        self.data_out = []

    def signal_in(self) -> int:
        if len(self.data_in) == 0:
            raise EOFError("end of data array")
        return ord(self.data_in.pop(0))

    def signal_out(self, data: int):
        self.data_out.append(chr(data))

    def get_received_data(self) -> list:
        return self.data_out
