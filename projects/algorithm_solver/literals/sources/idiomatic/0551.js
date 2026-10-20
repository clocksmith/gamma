class Solution {
  checkRecord(values) {
    return !/A[\s\S]*A|LLL/.test(values);
  }
}
