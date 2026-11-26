const line = require('fs').readFileSync('/dev/stdin', 'utf-8').split('\n');

let cnt = 0;

const merge = (arr, left, mid, right) => {
    const n1 = mid - left;
    const n2 = right - mid;
    const L = [];
    const R = [];

    for (let i = 0; i < n1; i++) {
        L[i] = arr[left + i];
    }
    for (let i = 0; i < n2; i++) {
        R[i] = arr[mid + i];
    }

    L[n1] = 1/0;
    R[n2] = 1/0;

    let i = 0;
    let j = 0;
    for (let k = left; k < right; k++) {
        cnt++;
        if (L[i] <= R[j]) {
            arr[k] = L[i];
            i++;
        } else {
            arr[k] = R[j];
            j++;
        }
    }
};

const msort = (arr, left, right) => {
    if (left + 1 < right) {
        const mid = Math.floor((left + right) / 2);
        msort(arr, left, mid);
        msort(arr, mid, right);
        merge(arr, left, mid, right);
    }
};

const data = line[1].split(' ').map(Number);
msort(data, 0, data.length);
console.log(data.join(' '));
console.log(cnt);

