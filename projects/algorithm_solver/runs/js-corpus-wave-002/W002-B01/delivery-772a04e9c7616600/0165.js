function compareVersion(version1, version2) {
  const first = version1.split('.');
  const second = version2.split('.');
  const count = Math.max(first.length, second.length);

  function normalize(revision) {
    const stripped = revision.replace(/^0+/, '');
    return stripped.length === 0 ? '0' : stripped;
  }

  for (let index = 0; index < count; index += 1) {
    const left = normalize(first[index] ?? '0');
    const right = normalize(second[index] ?? '0');

    if (left.length !== right.length) {
      return left.length < right.length ? -1 : 1;
    }
    if (left !== right) {
      return left < right ? -1 : 1;
    }
  }

  return 0;
}
