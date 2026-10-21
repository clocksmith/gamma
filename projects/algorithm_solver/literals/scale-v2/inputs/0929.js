function uniqueEmailCount(emailAddresses) {
  const normalizedAddresses = {};
  let resultCount = 0;
  for (const emailAddress of emailAddresses) {
    const emailParts = emailAddress.split("@");
    const localText = emailParts[0];
    const domainText = emailParts[1];
    const localCharacters = [];
    for (const character of localText) {
      if (character === ".") {
        continue;
      }
      if (character === "+") {
        break;
      }
      localCharacters.push(character);
    }
    const normalizedAddress = "$" + localCharacters.join("") + "@" + domainText;
    if (!normalizedAddresses[normalizedAddress]) {
      resultCount += 1;
      normalizedAddresses[normalizedAddress] = true;
    }
  }
  return resultCount;
}
class Solution {
  numUniqueEmails(emails) {
    return uniqueEmailCount(emails);
  }
}
