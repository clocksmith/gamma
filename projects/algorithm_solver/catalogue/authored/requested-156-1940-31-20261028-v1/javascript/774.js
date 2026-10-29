"use strict";

function solve(stations, k) {
  const gaps = new Float64Array(stations.length - 1);
  for (let i = 0; i < stations.length - 1; i++) {
    gaps[i] = stations[i + 1] - stations[i];
  }
  let lo = 0.0;
  let hi = stations[stations.length - 1] - stations[0];
  for (let iter = 0; iter < 60; iter++) {
    const mid = (lo + hi) * 0.5;
    let need = 0;
    for (let i = 0; i < gaps.length; i++) {
      need += Math.floor((gaps[i] - 1e-12) / mid);
    }
    if (need <= k) hi = mid;
    else lo = mid;
  }
  return Math.round(hi * 1e6) / 1e6;
}

function minmaxGasDist(stations, k) {
  return solve(stations, k);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.minmaxGasDist = minmaxGasDist;
