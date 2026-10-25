class Solution {
  corpFlightBookings(bookings, n) {
    const changes = Array(n + 1).fill(0);
    for (const [first, last, seats] of bookings) {
      changes[first - 1] += seats;
      changes[last] -= seats;
    }
    const output = [];
    let active = 0;
    for (let index = 0; index < n; index += 1) {
      active += changes[index];
      output.push(active);
    }
    return output;
  }
}
