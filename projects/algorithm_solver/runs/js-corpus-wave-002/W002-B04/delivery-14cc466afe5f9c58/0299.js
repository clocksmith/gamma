function getHint(secret, guess) {
  const counts = Array(10).fill(0);
  let bulls = 0, cows = 0;
  for (let i = 0; i < secret.length; i++) {
    if (secret[i] === guess[i]) bulls++;
    else counts[Number(secret[i])]++;
  }
  for (let i = 0; i < secret.length; i++) {
    if (secret[i] !== guess[i] && counts[Number(guess[i])] > 0) {
      cows++;
      counts[Number(guess[i])]--;
    }
  }
  return `${bulls}A${cows}B`;
}
