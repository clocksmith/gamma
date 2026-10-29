"""Original hack2hire:68771a6734c7f781dae2a98b; inferred public-preview contract; qualification unknown."""
class PaginationAPI:
    def __init__(self, external):
        self.external = external
        self.buffer = []
        self.offset = 0
        self.page = 0
        self.calls = 0
        self.eof = False

    def read(self, count):
        result = []
        while len(result) < count:
            if self.offset < len(self.buffer):
                result.append(self.buffer[self.offset])
                self.offset += 1
            elif self.eof:
                break
            else:
                self.buffer = list(self.external.getPage(self.page))
                self.page += 1
                self.calls += 1
                self.offset = 0
                if not self.buffer:
                    self.eof = True
        return result

    def fetchCount(self):
        return self.calls

class _ExternalPageFixture:
    def __init__(self, pages):
        self.pages = [list(page) for page in pages]

    def getPage(self, page):
        return list(self.pages[page]) if page < len(self.pages) else []

def solve(operation_names, argument_lists):
    if len(operation_names) != len(argument_lists) or not operation_names or operation_names[0] != 'PaginationAPI':
        raise ValueError("exact constructor trace required")
    instance = PaginationAPI(_ExternalPageFixture(argument_lists[0][0]))
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in ('read', 'fetchCount'):
            raise ValueError("unknown method")
        result.append(getattr(instance, name)(*arguments))
    return result
