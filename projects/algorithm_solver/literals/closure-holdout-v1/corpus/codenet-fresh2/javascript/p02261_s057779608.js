//config = { input: 'tmp', newline: '\r\n' }; // win
config = { input: '/dev/stdin', newline: '\n' }; // linux

A = require('fs').readFileSync(config.input, 'ascii')
  .split(config.newline, 2);
A = A[1].split(' ');

stable = [].concat(A);
stableSort(stable);

bubble = [].concat(A);
bubbleSort(bubble);
console.log(bubble.join(' '));
console.log(equal(bubble, stable) ? 'Stable' : 'Not stable');

selection = [].concat(A);
selectionSort(selection);
console.log(selection.join(' '));
console.log(equal(selection, stable) ? 'Stable' : 'Not stable');

function bubbleSort(C) {
  var i, j, tmp;
  for (i in C) {
    for (j = C.length - 1; j > i; j--) {
      if (C[j][1] < C[j-1][1]) {
        tmp = C[j];
        C[j] = C[j-1];
        C[j-1] = tmp;
      }
    }
  }
}

function selectionSort(C) {
  var i, minj, j, tmp;
  for (i in C) {
    minj = i;
    for (j = i; j < C.length; j++) {
      if (C[j][1] < C[minj][1])
        minj = j;
    }
    tmp = C[i];
    C[i] = C[minj];
    C[minj] = tmp;
  }
}

function stableSort(A) {
  var res, i, j;
  res = [];
  for (i = 1; i <= 9; i++) {
    for (j in A) {
      if (A[j][1] === String(i)) res.push(A[j]);
    }
  }
  for (i in A) A[i] = res[i];
}

function equal(A, B) {
  var i;
  for (i in A)
    if (A[i] !== B[i]) return false;
  return true;
}