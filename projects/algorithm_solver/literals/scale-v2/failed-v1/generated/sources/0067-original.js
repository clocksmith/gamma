/* 67. Add Binary */
function addBinary(a, b) {
  let leftIndex = a.length - 1,
    rightIndex = b.length - 1,
    carry = 0,
    result = '';
  while (leftIndex >= 0 || rightIndex >= 0 || carry) {
    const total = carry + (leftIndex >= 0 ? Number(a[leftIndex--]) : 0) + (rightIndex >= 0 ? Number(b[rightIndex--]) : 0);
    result = String(total % 2) + result;
    carry = Math.floor(total / 2);
  }
  return result;
}
