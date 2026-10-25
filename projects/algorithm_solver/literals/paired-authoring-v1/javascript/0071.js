class Solution {
  simplifyPath(path) {
    const components = [];
    for (const component of path.split("/")) {
      if (component === "" || component === ".") {
        continue;
      }
      if (component === "..") {
        if (components.length > 0) {
          components.pop();
        }
      } else {
        components.push(component);
      }
    }
    return "/" + components.join("/");
  }
}
