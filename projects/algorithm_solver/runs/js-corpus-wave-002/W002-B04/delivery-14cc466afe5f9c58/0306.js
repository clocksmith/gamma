function isAdditiveNumber(num) {
  function addStrings(a, b) {
    let i = a.length - 1, j = b.length - 1, carry = 0, result = '';
    while (i >= 0 || j >= 0 || carry) {
      const sum = (i >= 0 ? Number(a[i--]) : 0) + (j >= 0 ? Number(b[j--]) : 0) + carry;
      result = String(sum % 10) + result;
      carry = Math.floor(sum / 10);
    }
    return result;
  }
  for (let firstLength = 1; firstLength <= Math.floor(num.length / 2); firstLength++) {
    if (firstLength > 1 && num[0] === '0') break;
    for (let secondLength = 1; firstLength + secondLength < num.length; secondLength++) {
      if (secondLength > 1 && num[firstLength] === '0') break;
      let first = num.slice(0, firstLength), second = num.slice(firstLength, firstLength + secondLength);
      let index = firstLength + secondLength, terms = 2;
      while (index < num.length) {
        const next = addStrings(first, second);
        if (!num.startsWith(next, index)) break;
        index += next.length; first = second; second = next; terms++;
      }
      if (index === num.length && terms >= 3) return true;
    }
  }
  return false;
}
