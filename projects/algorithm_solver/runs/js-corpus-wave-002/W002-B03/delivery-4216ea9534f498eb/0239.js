function maxSlidingWindow(nums, k) {
  const deque = [], result = [];
  let front = 0;
  for (let i = 0; i < nums.length; i++) {
    while (front < deque.length && deque[front] <= i - k) front++;
    while (deque.length > front && nums[deque[deque.length - 1]] <= nums[i]) deque.pop();
    deque.push(i);
    if (i >= k - 1) result.push(nums[deque[front]]);
    if (front > 1024 && front * 2 > deque.length) { deque.splice(0, front); front = 0; }
  }
  return result;
}
