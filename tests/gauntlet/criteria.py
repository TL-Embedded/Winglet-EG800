import re
from .util import T, format_value

def format_value(value) -> str:
    if type(value) is str:
        return f'"{value}"'
    elif type(value) is bool:
        return "OK" if value else "ERROR"
    return str(value)


class Criteria():
    def evaluate(self, value: T) -> bool:
        raise NotImplementedError()
    
    def describe(self) -> str:
        raise NotImplementedError()


class NullCriteria(Criteria):
    def evaluate(self, value: T) -> bool:
        return True
    
    def describe(self) -> str:
        return ""


class EqualsCriteria(Criteria):
    def __init__(self, equals: T):
        self.equals = equals
    
    def evaluate(self, value: T) -> bool:
        return self.equals == value
    
    def describe(self) -> str:
        return f"x = {format_value(self.equals)}"


class NotFalseCriteria(Criteria):
    def evaluate(self, value: T) -> bool:
        return value != False
    
    def describe(self):
        return ""


class RangeCriteria(Criteria):
    def __init__(self, minimum: T, maximum: T):
        self.minimum = minimum
        self.maximum = maximum

    def evaluate(self, value: T):
        return (self.minimum == None or value >= self.minimum) and (self.maximum == None or value <= self.maximum)
    
    def describe(self) -> str:
        if self.maximum == None:
            return f"x < {format_value(self.minimum)}"
        if self.maximum == None:
            return f"x > {format_value(self.maximum)}"
        return f"{format_value(self.minimum)} < x < {format_value(self.maximum)}"


class PatternCriteria(Criteria):
    def __init__(self, pattern: str):
        self.pattern = pattern

    def evaluate(self, value: T):
        return re.match(self.pattern, value) != None
    
    def describe(self) -> str:
        return f"x matches \"{self.pattern}\""


class GroupCriteria(Criteria):
    def __init__(self, criteria: list[Criteria]):
        self.criteria = criteria

    def append(self, criteria: Criteria):
        self.criteria.append(criteria)

    def evaluate(self, value: T):
        return all(c.evaluate(value) for c in self.criteria)
    
    def describe(self):
        return " & ".join(c.describe() for c in self.criteria)
    