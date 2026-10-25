class Solution {
  killProcess(pid, ppid, kill) {
    const children = new Map();
    for (let index = 0; index < pid.length; index += 1) {
      const process = pid[index];
      const parent = ppid[index];
      if (!children.has(parent)) {
        children.set(parent, []);
      }
      children.get(parent).push(process);
    }
    const pending = [kill];
    const result = [];
    while (pending.length > 0) {
      const process = pending.pop();
      result.push(process);
      const descendants = children.get(process) || [];
      for (let index = descendants.length - 1; index >= 0; index -= 1) {
        pending.push(descendants[index]);
      }
    }
    return result;
  }
}
