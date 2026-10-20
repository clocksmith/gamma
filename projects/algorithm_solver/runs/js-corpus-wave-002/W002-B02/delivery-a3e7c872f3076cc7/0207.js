function canFinish(numCourses, prerequisites) {
  const outgoing = Array.from(
    { length: numCourses },
    () => []
  );
  const indegree = new Array(numCourses).fill(0);

  for (const [course, prerequisite] of prerequisites) {
    outgoing[prerequisite].push(course);
    indegree[course] += 1;
  }

  const queue = [];
  for (let course = 0; course < numCourses; course += 1) {
    if (indegree[course] === 0) {
      queue.push(course);
    }
  }

  let completed = 0;
  for (let start = 0; start < queue.length; start += 1) {
    const prerequisite = queue[start];
    completed += 1;

    for (const course of outgoing[prerequisite]) {
      indegree[course] -= 1;
      if (indegree[course] === 0) {
        queue.push(course);
      }
    }
  }

  return completed === numCourses;
}
