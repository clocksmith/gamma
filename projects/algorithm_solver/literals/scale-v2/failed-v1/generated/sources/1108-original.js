function defangIpv4Text(addressText) {
  return addressText.split(".").join("[.]");
}
class Solution {
  defangIPaddr(address) {
    return defangIpv4Text(address);
  }
}
