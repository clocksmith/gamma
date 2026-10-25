class Solution:
    def killProcess(self, pid: list[int], ppid: list[int], kill: int) -> list[int]:
        children = {}
        for process, parent in zip(pid, ppid):
            if parent not in children:
                children[parent] = []
            children[parent].append(process)
        queue = [kill]
        head = 0
        while head < len(queue):
            process = queue[head]
            head += 1
            for child in children.get(process, ()):
                queue.append(child)
        return queue
