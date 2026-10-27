// Original candidate; contract and evidence: ../batch1/manifest.json
"use strict";
function solve(nums) {
    let width = 1;
    for (const number of nums) while (width <= number) width *= 2;
    const values = new Float64Array(width);
    for (const number of nums) values[number] = 1;
    function transform() {
        for (let step = 1; step < width; step *= 2) {
            for (let start = 0; start < width; start += 2*step) {
                for (let offset = 0; offset < step; offset++) {
                    const a = values[start+offset], b = values[start+step+offset];
                    values[start+offset] = a+b;
                    values[start+step+offset] = a-b;
                }
            }
        }
    }
    transform();
    for (let i = 0; i < width; i++) values[i] = values[i] ** 3;
    transform();
    let answer = 0;
    for (const value of values) if (value > 0) answer++;
    return answer;
}
module.exports = {solve};
