class Solution {
  findRestaurant(list1, list2) {
    const positions = new Map();
    for (let index = 0; index < list1.length; index += 1) {
      positions.set(list1[index], index);
    }
    let best_sum = list1.length + list2.length;
    let result = [];
    for (let index = 0; index < list2.length; index += 1) {
      const name = list2[index];
      if (!positions.has(name)) {
        continue;
      }
      const index_sum = positions.get(name) + index;
      if (index_sum < best_sum) {
        best_sum = index_sum;
        result = [name];
      } else if (index_sum === best_sum) {
        result.push(name);
      }
    }
    return result;
  }
}
