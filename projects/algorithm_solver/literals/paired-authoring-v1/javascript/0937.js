function compareLetterLogs(left, right) {
  for (let field = 0; field < 3; field += 1) {
    if (left[field] < right[field]) {
      return -1;
    }
    if (left[field] > right[field]) {
      return 1;
    }
  }
  return 0;
}

class Solution {
  reorderLogFiles(logs) {
    const letters = [];
    const digits = [];
    for (let index = 0; index < logs.length; index += 1) {
      const log = logs[index];
      const separator = log.indexOf(" ");
      const identifier = log.slice(0, separator);
      const content = log.slice(separator + 1);
      if (content[0] >= "0" && content[0] <= "9") {
        digits.push(log);
      } else {
        letters.push([content, identifier, index, log]);
      }
    }
    letters.sort(compareLetterLogs);
    const result = [];
    for (const record of letters) {
      result.push(record[3]);
    }
    for (const log of digits) {
      result.push(log);
    }
    return result;
  }
}
