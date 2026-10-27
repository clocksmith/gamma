# Original implementation. Contract: https://leetcode.com/problems/minimum-number-of-operations-to-sort-a-binary-tree-by-level/
def solve(root_level_order):
    if not root_level_order:return 0
    # Standard queue serialization: null entries do not themselves have children.
    levels=[];queue=[(root_level_order[0],0)];head=0;pos=1
    while head<len(queue):
        value,depth=queue[head];head+=1
        if len(levels)==depth:levels.append([])
        levels[depth].append(value)
        for _ in range(2):
            if pos<len(root_level_order):
                child=root_level_order[pos];pos+=1
                if child is not None:queue.append((child,depth+1))
    answer=0
    for level in levels:
        ranks={v:i for i,v in enumerate(sorted(level))};p=[ranks[x] for x in level];seen=set()
        for i in range(len(p)):
            if i in seen:continue
            j=i;size=0
            while j not in seen:seen.add(j);size+=1;j=p[j]
            answer+=size-1
    return answer
