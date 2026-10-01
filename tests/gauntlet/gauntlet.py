from typing import Callable
import time, datetime

from .criteria import *
from .exporters import *
from .util import T, format_value


class Gauntlet():
    
    def __init__(self, name: str):
        self.name = name
        self.running = False
        self.exporters: list[Exporter] = [
            ConsoleExporter()
        ]

    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.stop()
    
    def start(self):
        self.running = True
        self.passed_tests = 0
        self.total_tests = 0
        self.start_time = time.time()
        ts = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S.%f")[:-3]

        for exporter in self.exporters:
            exporter.open()

        r = Result("Test started", self.elapsed())
        r.result = ts
        self._log(r)

    def stop(self):
        self.running = False

        r = Result("Test finished", self.elapsed())
        r.result = f"{self.passed_tests} / {self.total_tests} steps passed"
        r.status = "PASS" if self.passed_tests == self.total_tests else "FAIL"
        self._log(r, final=True)

        for exporter in self.exporters:
            exporter.close()

    def step(self, name: str,) -> 'Gauntlet.Step':
        return Gauntlet.Step(self, name)
    
    def elapsed(self) -> float:
        return time.time() - self.start_time
    
    def to_file(self, name: str = None, directory: str = "./results") -> 'Gauntlet':
        if name == None:
            name = self.name
        self.exporters.append(FileExporter(name, directory))
        return self
    
    def _log(self, result: Result, temporary: bool = False, final: bool = False):
        for exporter in self.exporters:
            exporter.write(result, temporary, final)

    def _log_step(self, result: Result, temporary: bool = False):
        if not temporary:
            self.total_tests += 1
            if result.status == "PASS":
                self.passed_tests += 1
            else:
                self.running = False
        self._log(result, temporary)

    class Step():
        def __init__(self, host: 'Gauntlet', name: str):
            self.gauntlet = host
            self.name = name
            self.result: T = None
            self.unit: str = None
            self.status = "RUN"
            self.function = None
            self.criteria: Criteria = NullCriteria()

        def run(self, skip = False) -> T:
            if skip or not self.gauntlet.running:
                self.status = "SKIP"
                self._log_result()
                return None
            
            if self.function:
                self._log_result(temporary=True)

                try:
                    self.result = self.function()
                except Exception as e:
                    self.status = "FAIL"
                    self.result = e
                    self._log_result()
                    return None
            
            passing = self.criteria.evaluate(self.result)
            self.status = "PASS" if passing else "FAIL"

            self._log_result()
            return self.result
        
        def _log_result(self, temporary: bool = False):
            r = Result(self.name, self.gauntlet.elapsed())
            r.result = format_value(self.result)
            r.unit = self.unit
            r.criteria = self.criteria.describe()
            r.status = self.status
            self.gauntlet._log_step(r, temporary)
            
        def set(self, value: T, unit: str = None) -> 'Gauntlet.Step':
            self.result = value
            self.unit = unit
            return self
        
        def measure(self, function: Callable[[], T], unit: str = None) -> 'Gauntlet.Step':
            self.function = function
            self.unit = unit
            return self
        
        def operation(self, function: Callable[[], None]) -> 'Gauntlet.Step':
            self.function = lambda: function() or True
            return self.equals(True)
        
        def equals(self, value: T) -> 'Gauntlet.Step':
            return self.add_criteria( EqualsCriteria(value) )

        def within(self, minimum: T, maximum: T) -> 'Gauntlet.Step':
            return self.add_criteria( RangeCriteria(minimum, maximum) )
        
        def minimum(self, minimum: T) -> 'Gauntlet.Step':
            return self.add_criteria( RangeCriteria(minimum=minimum) )
        
        def maximum(self, maximum: T) -> 'Gauntlet.Step':
            return self.add_criteria( RangeCriteria(maximum=maximum) )
        
        def pattern(self, pattern: str) -> 'Gauntlet.Step':
            return self.add_criteria( PatternCriteria(pattern) )

        def add_criteria(self, criteria: Criteria) -> 'Gauntlet.Step':
            if type(self.criteria) is NullCriteria:
                self.criteria = criteria
            elif type(self.criteria) is GroupCriteria:
                self.criteria.append(criteria)
            else:
                self.criteria = GroupCriteria([self.criteria, criteria])
            return self



