function numberToWords(num) {
  if (num === 0) return 'Zero';
  const small = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen'];
  const tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'];
  const units = ['', 'Thousand', 'Million', 'Billion'];
  function chunk(n) {
    const words = [];
    if (n >= 100) { words.push(small[Math.floor(n / 100)], 'Hundred'); n %= 100; }
    if (n >= 20) { words.push(tens[Math.floor(n / 10)]); n %= 10; }
    if (n > 0) words.push(small[n]);
    return words.join(' ');
  }
  const parts = [];
  let unit = 0;
  while (num > 0) {
    const group = num % 1000;
    if (group) parts.unshift([chunk(group), units[unit]].filter(Boolean).join(' '));
    num = Math.floor(num / 1000);
    unit++;
  }
  return parts.join(' ');
}
