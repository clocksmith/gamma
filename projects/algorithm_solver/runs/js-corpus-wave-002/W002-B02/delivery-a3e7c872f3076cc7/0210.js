function findOrder(numCourses, prerequisites) {
  const outgoing = Array.from(
    { length: numCourses },
    () => []
  );
  const indegree = new Array(numCourses).fill(0);

  for (const [course, prerequisite] of prerequisites) {
    outgoing[prerequisite].push(course);
    indegree[course] += 1;
  }

  const order = [];
  for (let course = 0; course < numCourses; course += 1) {
    if (indegree[course] === 0) {
      order.push(course);
    }
  }

  for (let start = 0; start < order.length; start += 1) {
    const prerequisite = order[start];

    for (const course of outgoing[prerequisite]) {
      indegree[course] -= 1;
      if (indegree[course] === 0) {
        order.push(course);
      }
    }
  }

  return order.length === numCourses ? order : [];
}
