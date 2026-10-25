class Solution {
  convert(s, numRows) {
    if (numRows === 1 || numRows >= s.length) {
      return s;
    }

    const rows = [];
    for (let index = 0; index < numRows; index += 1) {
      rows.push([]);
    }
    let row = 0;
    let direction = 1;
    for (let index = 0; index < s.length; index += 1) {
      rows[row].push(s[index]);
      if (row === 0) {
        direction = 1;
      } else if (row === numRows - 1) {
        direction = -1;
      }
      row += direction;
    }
    const ordered = [];
    for (const characters of rows) {
      ordered.push(characters.join(""));
    }
    return ordered.join("");
  }
}
