class Solution:
    def simplifyPath(self, path: str) -> str:
        components = []
        for component in path.split("/"):
            if component == "" or component == ".":
                continue
            if component == "..":
                if components:
                    components.pop()
            else:
                components.append(component)
        return "/" + "/".join(components)
