class Solution {
  prevPermOpt1(arr) {
    let pivot = arr.length - 2;
    while (pivot >= 0 && arr[pivot] <= arr[pivot + 1]) {
      pivot -= 1;
    }
    if (pivot < 0) {
      return arr;
    }
    let replacement = arr.length - 1;
    while (arr[replacement] >= arr[pivot]) {
      replacement -= 1;
    }
    while (replacement > pivot + 1 && arr[replacement - 1] === arr[replacement]) {
      replacement -= 1;
    }
    [arr[pivot], arr[replacement]] = [arr[replacement], arr[pivot]];
    return arr;
  }
}
