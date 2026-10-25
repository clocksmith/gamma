class Solution {
  prisonAfterNDays(cells, n) {
    function nextDay(state) {
      const following = new Array(8).fill(0);
      for (let index = 1; index < 7; index += 1) {
        following[index] = state[index - 1] === state[index + 1] ? 1 : 0;
      }
      return following;
    }

    let state = cells.slice();
    const seen = new Map();
    let day = 0;
    while (day < n) {
      const key = state.join("");
      if (seen.has(key)) {
        const remaining = (n - day) % (day - seen.get(key));
        for (let step = 0; step < remaining; step += 1) state = nextDay(state);
        return state;
      }
      seen.set(key, day);
      state = nextDay(state);
      day += 1;
    }
    return state;
  }
}
