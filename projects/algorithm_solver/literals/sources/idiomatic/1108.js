class Solution {
  defangIPaddr(values) {
    return values.replaceAll('.', '[.]');
  }
}
