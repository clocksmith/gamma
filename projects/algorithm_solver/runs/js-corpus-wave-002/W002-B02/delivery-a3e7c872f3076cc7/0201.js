function rangeBitwiseAnd(left, right) {
  let lower = left >>> 0;
  let upper = right >>> 0;
  let shifts = 0;

  while (lower !== upper) {
    lower >>>= 1;
    upper >>>= 1;
    shifts += 1;
  }

  return lower * (2 ** shifts);
}
