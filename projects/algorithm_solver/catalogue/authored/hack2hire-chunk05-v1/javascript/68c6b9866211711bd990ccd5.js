// Original hack2hire:68c6b9866211711bd990ccd5; inferred public-preview contract; qualification unknown.
"use strict";
function retry(operation, maxAttempts, initialDelay=0, multiplier=1, onDelay=null) {
  if (maxAttempts < 1) throw new Error('maxAttempts must be positive');
  let delay = initialDelay;
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try { return operation(); } catch (error) { if (attempt+1 === maxAttempts) throw error; }
    if (onDelay) onDelay(delay);
    delay *= multiplier;
  }
}
function retryOperation(outcomes, maxAttempts, initialDelay, multiplier) {
  let count = 0; const delays = [];
  const operation = () => {
    const entry = count < outcomes.length ? outcomes[count] : {error:'exhausted'}; count++;
    if (Object.prototype.hasOwnProperty.call(entry,'ok')) return structuredClone(entry.ok);
    throw new Error(entry.error);
  };
  try { const value = retry(operation, maxAttempts, initialDelay, multiplier, delay => delays.push(delay)); return {value, error:null, attempts:count, delays}; }
  catch (error) { return {value:null, error:error.message, attempts:count, delays}; }
}

const solve = retryOperation;
module.exports = solve;
module.exports.retryOperation = retryOperation;
module.exports.Solution = class { retryOperation(...args) { return retryOperation(...args); } };
module.exports.retry = retry;
