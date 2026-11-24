'use strict';

const input = require('fs').readFileSync('/dev/stdin', 'utf8').trim().split('\n');
const N = parseInt(input[0]);
const s = input[1];

function constructorAnswer(t1, t2, N, s) {
    let t = [t1, t2];

    let tNow = t2,
        tPrev = t1,
        tOdd = t1 == 'S' ? 'W' : 'S';

    for (let i = 1; i < N - 1; i++) {
        tNow = t[i];

        t.push(
            tNow == 'S' ?
            (s[i] == 'o' ? tPrev : tOdd) :
            (s[i] == 'o' ? tOdd : tPrev)
        );

        tPrev = tNow;
        tOdd = tPrev == 'S' ? 'W' : 'S';
    }

    return t;
}

function judge(t, N, s) {
    let s1 = s[0],
        sn = s[N-1],
        t1 = t[0],
        t2 = t[1],
        tn = t[N - 1],
        tn1 = t[N - 2];

    return (t1 == 'S' ?
        ((s1 == 'o') == (tn == t2)) :
        ((s1 == 'o') == (tn != t2)))
        &&
        (tn == 'S' ?
        ((sn == 'o') == (tn1 == t1)) :
        ((sn == 'o') == (tn1 != t1)));
}

let answerList = [
    ['S', 'S'],
    ['S', 'W'],
    ['W', 'S'],
    ['W', 'W'],
];

for (let i = 0; i < answerList.length; i++) {
    let t1 = answerList[i][0],
        t2 = answerList[i][1];

    let t = constructorAnswer(t1, t2, N, s);
    if (judge(t, N, s)) {
        console.log(t.join(''));
        process.exit(0);
    }
}

console.log('-1');