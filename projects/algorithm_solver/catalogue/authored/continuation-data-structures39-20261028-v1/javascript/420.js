"use strict";

function solve(password) {
  const n = password.length;
  let hasLower = false, hasUpper = false, hasDigit = false;
  for (let i = 0; i < n; i++) {
    const c = password[i];
    if (c >= "a" && c <= "z") hasLower = true;
    else if (c >= "A" && c <= "Z") hasUpper = true;
    else if (c >= "0" && c <= "9") hasDigit = true;
  }
  const missing = (hasLower ? 0 : 1) + (hasUpper ? 0 : 1) + (hasDigit ? 0 : 1);

  const runs = [];
  let i = 0;
  while (i < n) {
    let j = i;
    while (j < n && password[j] === password[i]) j++;
    if (j - i >= 3) runs.push(j - i);
    i = j;
  }

  if (n < 6) return Math.max(6 - n, missing);
  if (n <= 20) {
    let rep = 0;
    for (let k = 0; k < runs.length; k++) rep += Math.floor(runs[k] / 3);
    return Math.max(missing, rep);
  }

  const deletes = n - 20;
  let rem = deletes;
  for (let mod = 0; mod <= 1; mod++) {
    const need = mod + 1;
    for (let idx = 0; idx < runs.length; idx++) {
      if (rem < need) break;
      if (runs[idx] >= 3 && runs[idx] % 3 === mod) {
        runs[idx] -= need;
        rem -= need;
      }
    }
  }
  for (let idx = 0; idx < runs.length; idx++) {
    while (runs[idx] >= 3 && rem >= 3) {
      runs[idx] -= 3;
      rem -= 3;
    }
  }
  let replacements = 0;
  for (let idx = 0; idx < runs.length; idx++) {
    if (runs[idx] >= 3) replacements += Math.floor(runs[idx] / 3);
  }
  return deletes + Math.max(missing, replacements);
}

function strongPasswordChecker(password) {
  return solve(password);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.strongPasswordChecker = strongPasswordChecker;
