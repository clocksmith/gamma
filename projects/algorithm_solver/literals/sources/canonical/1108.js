class Solution {
  defangIPaddr(values) {
    return values.split(".").join("[.]");
  }
}
