"use strict";
function Main(input) {
    let In = new Inputer(input);
    let N = In.getInt(), M = In.getInt(), Q = In.getInt();
    let T = new Array(N+1).fill(0).map(() => new Array(N+1).fill(0));
    for (let m = 0; m < M; m++) {
        let l = In.getInt(), r = In.getInt();
        T[l][r] += 1;
    }
    for (let p = 1; p <= N; p++) {
        for (let q = 1; q <= N; q++) {
            T[p][q] += (T[p - 1][q] + T[p][q - 1] - T[p - 1][q - 1]);
        }
    }
    for (let n = 0; n < Q; n++) {
        let p = In.getInt(), q = In.getInt();
        console.log(T[q][q] - T[p - 1][q]);
    }
}
class Inputer {
    constructor (input) {
        this.cnt = 0;
        this.items = input.split(/\n|\s/);
    }
    getInt() {
        return this.items[this.cnt++] - 0;
    }
    getIntArray(N) {
        let array = new Array(N);
        for (let n = 0; n < N; n++) array[n] = getInt();
        return array;
    }
    getStr() {
        return this.items[this.cnt++];
    }
    getStrArray(N) {
        let array = new Array(N);
        for (let n = 0; n < N; n++) array[n] = getStr();
        return array;
    }
}
if (typeof window == "undefined") Main(require("fs").readFileSync("/dev/stdin", "utf8"));