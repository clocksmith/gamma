function solve(s) {
    const counts = Array(26).fill(0);
    for (const character of s) ++counts[character.charCodeAt(0) - 97];
    const pieces = [];
    let middle = '';
    for (let i = 0; i < 26; ++i) {
        const character = String.fromCharCode(97 + i);
        pieces.push(character.repeat(Math.floor(counts[i] / 2)));
        if (counts[i] % 2) middle = character;
    }
    const half = pieces.join('');
    return half + middle + [...half].reverse().join('');
}
module.exports = {solve};
