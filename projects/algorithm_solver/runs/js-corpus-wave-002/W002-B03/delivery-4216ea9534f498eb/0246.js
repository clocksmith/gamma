function isStrobogrammatic(num) {
  const pairs = { '0': '0', '1': '1', '6': '9', '8': '8', '9': '6' };
  for (let i = 0; i < num.length; i++) if (pairs[num[i]] !== num[num.length - i - 1]) return false;
  return true;
}
