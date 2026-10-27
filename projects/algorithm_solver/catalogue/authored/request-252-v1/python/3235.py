# Original candidate; contract and evidence: ../batch1/manifest.json
def solve(xCorner, yCorner, circles):
    n = len(circles)
    parent = list(range(n + 2))
    size = [1] * (n + 2)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            if size[a] < size[b]:
                a, b = b, a
            parent[b] = a
            size[a] += size[b]

    for i, (x, y, r) in enumerate(circles):
        rr = r * r
        if x*x + y*y <= rr or (x-xCorner)**2 + (y-yCorner)**2 <= rr:
            return False
        dx, dy = max(0, x-xCorner), max(0, y-yCorner)
        # The two boundary arcs join at the forbidden start/end corners.
        if x*x + dy*dy <= rr or (y-yCorner)**2 + dx*dx <= rr:
            union(i, n)
        if y*y + dx*dx <= rr or (x-xCorner)**2 + dy*dy <= rr:
            union(i, n + 1)
        for j in range(i):
            a, b, radius = circles[j]
            total = r + radius
            if (x-a)**2 + (y-b)**2 > total*total:
                continue
            # This radius-weighted point lies in both intersecting disks.
            # If it is outside an upper/right side, a relevant clipped overlap
            # is already connected through that same rectangle boundary arc.
            if x*radius + a*r <= xCorner*total and y*radius + b*r <= yCorner*total:
                union(i, j)
        if find(n) == find(n + 1):
            return False
    return True
