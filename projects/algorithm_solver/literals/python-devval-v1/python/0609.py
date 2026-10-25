def solve(descriptions):
    groups = {}
    for description in descriptions:
        fields = description.split()
        directory = fields[0]
        for item in fields[1:]:
            opening = item.index("(")
            content = item[opening + 1:-1]
            path = directory + "/" + item[:opening]
            groups.setdefault(content, []).append(path)
    return [paths for paths in groups.values() if len(paths) > 1]
