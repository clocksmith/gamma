"use strict";

function solve(sensor1, sensor2) {
  const n = sensor1.length;
  let i = 0;
  while (i < n && sensor1[i] === sensor2[i]) i++;
  if (i >= n - 1) return -1;
  let ok1 = true, ok2 = true;
  for (let j = i; j < n - 1; j++) {
    if (sensor1[j] !== sensor2[j + 1]) ok1 = false;
    if (sensor2[j] !== sensor1[j + 1]) ok2 = false;
  }
  if (ok1 && !ok2) return 1;
  if (ok2 && !ok1) return 2;
  return -1;
}

function badSensor(sensor1, sensor2) {
  return solve(sensor1, sensor2);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.badSensor = badSensor;
