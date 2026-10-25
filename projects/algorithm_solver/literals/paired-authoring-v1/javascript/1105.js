class Solution {
  minHeightShelves(books, shelfWidth) {
    const best = Array(books.length + 1).fill(0);
    for (let end = 1; end <= books.length; end += 1) {
      best[end] = best[end - 1] + books[end - 1][1];
      let width = 0;
      let height = 0;
      for (let start = end - 1; start >= 0; start -= 1) {
        width += books[start][0];
        if (width > shelfWidth) {
          break;
        }
        height = Math.max(height, books[start][1]);
        best[end] = Math.min(best[end], best[start] + height);
      }
    }
    return best[books.length];
  }
}
