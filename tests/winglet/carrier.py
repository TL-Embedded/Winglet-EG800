from . import SCPI

class Carrier():
    def __init__(self, uri: str = None):
        if uri == None:
            uri = Carrier.find_devices()[0]
        self.scpi = SCPI.from_uri(uri)

    def is_present(self, throw_on_error: bool = False) -> bool:
        success = self.scpi.get_idn().startswith("TL-Embedded, Winglet-Carrier,")
        self.scpi.read() # Dummy read, because we accidentally send an extra line
        if throw_on_error and not success:
            raise Exception("Wingler carrier not found")
        return success

    def close(self):
        self.scpi.close()

    def reset(self):
        self.scpi.write("*RST")

    def set_power(self, enable: bool):
        self.scpi.write(f"POW {'ON' if enable else 'OFF'}")

    def set_dtr(self, enable: bool):
        self.scpi.write(f"IO:DTR {'ON' if enable else 'OFF'}")

    def get_dcd(self) -> bool:
        result = self.scpi.query("IO:DCD?")
        return result == "ON"

    def set_wake(self, enable: bool):
        self.scpi.write(f"IO:WAKE {'ON' if enable else 'OFF'}")

    def set_reset(self, enable: bool):
        self.scpi.write(f"IO:RST {'ON' if enable else 'OFF'}")

    def detect_eeprom(self) -> bool:
        result = self.scpi.query("PROM?")
        return result == "ON"

    def read_eeprom(self) -> str | None:
        result = self.scpi.query("PROM:READ?")
        if result.startswith('"') and result.endswith('"'):
            return result[1:-1]
        return None

    def write_eeprom(self, text: str):
        self.scpi.write(f"PROM:WRITE \"{text}\"")

    def enable_uart(self, port: int, enable: bool, baud: int = 115200, swap: bool = False):
        if enable:
            self.scpi.write(f"UART{port}:BAUD {baud}")
            self.scpi.write(f"UART{port}:SWAP {'ON' if swap else 'OFF'}")
            self.scpi.write(f"UART{port}:EN ON")
        else:
            self.scpi.write(f"UART{port}:EN OFF")

    def find_uart(self, port: int):
        devname = self.scpi._port.port # Filthy hack
        interface_no = str(2 * port)
        from serial.tools.list_ports import comports
        ports = comports()
        path = self._find_port_with(ports, {"device": devname}).device_path[:-1]
        return self._find_port_with(ports, {"device_path": path + interface_no}).device

    @staticmethod
    def find_devices() -> list[str]:
        from serial.tools.list_ports import comports
        items = []
        for port in comports():
            if port.manufacturer == "Lambosaurus" and port.product == "STM32X":
                interface = int(port.device_path.split('.')[-1])
                if interface == 0:
                    items.append("tty:" + port.device)
        return items

    def _find_port_with(self, ports, kvs: dict):
        for port in ports:
            if all( getattr(port, k) == v for k,v in kvs.items() ):
                return port
        raise Exception(f"Cannot find port with criteria {kvs}")
