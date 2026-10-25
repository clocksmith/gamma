class Solution:
    def killProcess(self, pid: list[int], ppid: list[int], kill: int) -> list[int]:
        children = {}
        for process, parent in zip(pid, ppid):
            if parent not in children:
                children[parent] = []
            children[parent].append(process)
        pending = [kill]
        result = []
        while pending:
            process = pending.pop()
            result.append(process)
            for child in reversed(children.get(process, ())):
                pending.append(child)
        return result
