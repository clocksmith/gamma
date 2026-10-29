"""Hack2Hire 69026c73d18315042523a913 (Design an Interactive Paginator) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class Paginator:
    def __init__(self, totalPages, visibleCount, currentPage):
        self.total = totalPages
        self.visible = visibleCount
        self.current = min(max(currentPage, 1), totalPages)

    @staticmethod
    def render(totalPages, visibleCount, currentPage):
        shown = min(visibleCount, totalPages)
        start = max(1, min(currentPage - (visibleCount - 1) // 2, totalPages - shown + 1))
        end = start + shown - 1
        parts = []
        if currentPage > 1:
            parts.append('<')
        if start > 1:
            parts.append('...')
        for page in range(start, end + 1):
            parts.append('[%d]' % page if page == currentPage else str(page))
        if end < totalPages:
            parts.append('...')
        if currentPage < totalPages:
            parts.append('>')
        return ' '.join(parts)

    def _move(self, page):
        self.current = min(max(page, 1), self.total)
        return Paginator.render(self.total, self.visible, self.current)

    def next(self):
        return self._move(self.current + 1)

    def prev(self):
        return self._move(self.current - 1)

    def goTo(self, page):
        return self._move(page)


def solve(operation_names, argument_lists):
    if operation_names[0] != 'Paginator' or len(argument_lists[0]) != 3:
        raise ValueError('exact initial constructor required')
    instance = Paginator(*argument_lists[0])
    allowed = {'next', 'prev', 'goTo'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
