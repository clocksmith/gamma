# Original candidate. Contract: https://leetcode.com/problems/step-by-step-directions-from-a-binary-tree-node-to-another/
def solve(root, startValue, destValue):
    parent={root[0]:(None,'')};q=[root[0]];i=1
    for node in q:
        for direction in 'LR':
            if i<len(root):
                child=root[i];i+=1
                if child is not None:parent[child]=(node,direction);q.append(child)
    ancestors={};u=startValue;steps=0
    while u is not None:ancestors[u]=steps;steps+=1;u=parent[u][0]
    down=[];u=destValue
    while u not in ancestors:
        v,d=parent[u];down.append(d);u=v
    return 'U'*ancestors[u]+''.join(reversed(down))
