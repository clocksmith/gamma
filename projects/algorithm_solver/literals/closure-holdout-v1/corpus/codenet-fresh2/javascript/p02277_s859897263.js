class Card {
  constructor(mark, value) {
    this.mark = String(mark);
    this.value = Number(value);
  }

  equals(other) { return this.value === other.value && this.mark === other.mark; }

  compareTo(other) {
    if (this.value === other.value) return 0;
    else if (this.value < other.value) return -1;
    else return 1;
  }

  toString() { return `${this.mark} ${this.value}` }
}

(function main(){
  const lines = require('fs').readFileSync('/dev/stdin', 'utf8').trim().split('\n');
  const n = Number(lines.shift());
  const arr = lines.map(r => r.split(' ')).map(c => new Card(c[0], c[1]));
  const quick_arr = Array.from(arr);

  quickSort(quick_arr, 0, n - 1);
  const isStable = arr.map((e, idx) => ({val: e, idx: idx}))
      .sort((a, b) => a.val.compareTo(b.val) || a.idx - b.idx)
      .every((card, i) => card.val.equals(quick_arr[i]));

  console.log(isStable ? 'Stable' : 'Not stable');
  console.log(quick_arr.join('\n'));
})();

function quickSort(arr, p, r) {
  const partition = function(arr, p, r) {
     let x  = arr[r];
     let i = p - 1;
     for (let j = p; j < r; j++) {
       if (arr[j].compareTo(x) <= 0) {
         i++;
         [arr[i], arr[j]] = [arr[j], arr[i]];
       }
     }
     [arr[i + 1], arr[r]] = [arr[r], arr[i + 1]];
     return i + 1;
  }

  quickSort = function(arr, p, r) {
    if (p < r) {
      let q = partition(arr, p, r);
      quickSort(arr, p, q - 1);
      quickSort(arr, q + 1, r);
    }
  }
  quickSort(arr, p, r);
}

