function isSelfCrossing(distance) {
  for (let index = 3; index < distance.length; index++) {
    if (distance[index] >= distance[index - 2] &&
      distance[index - 1] <= distance[index - 3]) return true;

    if (index >= 4 && distance[index - 1] === distance[index - 3] &&
      distance[index] + distance[index - 4] >= distance[index - 2]) return true;

    if (index >= 5 && distance[index - 2] >= distance[index - 4] &&
      distance[index - 1] <= distance[index - 3] &&
      distance[index - 1] + distance[index - 5] >= distance[index - 3] &&
      distance[index] + distance[index - 4] >= distance[index - 2]) return true;
  }
  return false;
}
