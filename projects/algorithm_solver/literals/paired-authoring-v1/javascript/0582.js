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
    const queue = [kill];
    let head = 0;
    while (head < queue.length) {
      const process = queue[head];
      head += 1;
      for (const child of children.get(process) || []) {
        queue.push(child);
      }
    }
    return queue;
  }
}
