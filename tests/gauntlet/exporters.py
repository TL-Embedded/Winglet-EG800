from .util import console_color
import os, shutil

MD_COLUMNS = [8, 28, 30, 6, 28, 7]
MD_COLUMNS_TOTAL = sum(MD_COLUMNS) + (len(MD_COLUMNS) * 2) + 1
MD_HEADERS = ["Time", "Step", "Result", "Unit", "Criteria", "Status"]
MD_COL_STATUS = MD_HEADERS.index("Status")

class Result():
    def __init__(self, name: str, timestamp: float):
        self.name = name
        self.unit: str = None
        self.result: str = None
        self.criteria: str = None
        self.status: str = None
        self.timestamp = timestamp


class Exporter():
    def open(self):
        pass

    def close(self):
        pass

    def write(self, result: Result, temporary: bool = False, final: bool = False):
        raise NotImplementedError()


class ConsoleExporter(Exporter):
    def open(self):
        self._write_row(MD_HEADERS)
        self._write_row(["-" * (c-1) for c in MD_COLUMNS])

    def write(self, result: Result, temporary: bool = False, final: bool = False):
        self._write_row([
            f"{result.timestamp:7.03f}",
            result.name,
            result.result or "",
            result.unit or "",
            result.criteria or "",
            result.status or ""
        ], temporary, final)
        
    def _write_row(self, items: list, temporary: bool = False, final: bool = False):

        if temporary and shutil.get_terminal_size().columns < 120:
            return

        code = {
            "PASS": 'g',
            "FAIL": 'r',
            "RUN": 'y',
            "SKIP": 'f',
        }.get(items[MD_COL_STATUS], None)

        full_row = code == 'f' or final
        if final and code and code != 'f':
            code += 'b'

        for i, width in enumerate(MD_COLUMNS):
            items[i] = items[i].ljust(width)

        if code and not full_row:
            items[MD_COL_STATUS] = console_color(items[MD_COL_STATUS], code)

        text = "| " + "| ".join(items) + "|"
        if code and full_row:
            text = console_color(text, code)

        if temporary:
            print(text, end="\r", flush=True)
        else:
            print(text)


class FileExporter(Exporter):
    def __init__(self, name: str, directory: str = "./results"):
        os.makedirs(directory, exist_ok=True)
        name, extn = os.path.splitext(name)
        path = self._unique_filename(directory, name, extn or ".md")
        self.file = open(path, 'w')

    def _unique_filename(self, directory: str, name: str, extn: str) -> str:
        fnames = os.listdir(directory)
        for i in range(1000000):
            candidate = f"{name}.{i}{extn}"
            if candidate not in fnames:
                return os.path.join(directory, candidate)
        raise Exception("Could not find free filename!")

    def open(self):
        self._write_row(MD_HEADERS)
        self._write_row(["-" * (c-1) for c in MD_COLUMNS])

    def close(self):
        self.file.close()

    def write(self, result: Result, temporary: bool = False, final: bool = False):
        if temporary:
            return
        
        self._write_row([
            f"{result.timestamp:7.03f}",
            result.name,
            result.result or "",
            result.unit or "",
            result.criteria or "",
            result.status or ""
        ])
        
    def _write_row(self, items: list):
        for i, width in enumerate(MD_COLUMNS):
            items[i] = items[i].ljust(width)
        self.file.write("| " + "| ".join(items) + "|\n")
