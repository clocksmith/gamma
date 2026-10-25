class Solution {
  minMovesToSeat(seats, students) {
    const orderedSeats = seats.slice().sort((first, second) => first - second);
    const orderedStudents = students.slice().sort((first, second) => first - second);
    let total = 0;
    for (let index = 0; index < orderedSeats.length; index += 1) {
      total += Math.abs(orderedSeats[index] - orderedStudents[index]);
    }
    return total;
  }
}
