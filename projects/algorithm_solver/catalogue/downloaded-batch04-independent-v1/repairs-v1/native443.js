function gamma_native443(chars) {
  const length = new Solution().compress(chars);
  if (!Number.isInteger(length)) return {bad_length_type: typeof length};
  return {length, prefix: chars.slice(0, length)};
}
