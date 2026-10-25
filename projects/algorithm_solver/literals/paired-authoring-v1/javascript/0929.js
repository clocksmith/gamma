class Solution {
  numUniqueEmails(emails) {
    const addresses = new Set();
    for (const email of emails) {
      const [local, domain] = email.split("@");
      const normalized = local.split("+")[0].split(".").join("");
      addresses.add(normalized + "@" + domain);
    }
    return addresses.size;
  }
}
