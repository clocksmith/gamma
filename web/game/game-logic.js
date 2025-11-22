import { MathUtils } from '../utils/math.js';

export function generateChoices(topTokens, engine, numChoices = 4) {
  const filtered = topTokens.filter(token => {
    const text = token.text;
    if (engine.isSpecialToken(token.id)) return false;
    if (/^[<>\[\]{}()=+*\/]/.test(text)) return false;
    if (!/\S/.test(text)) return false;
    return true;
  });

  if (filtered.length < numChoices) {
    const choices = topTokens.slice(0, numChoices);
    return {
      choices,
      correctIndex: 0,
      correctToken: choices[0]
    };
  }

  const correct = filtered[0];
  const distractors = filtered.slice(1, numChoices);

  const choices = [correct, ...distractors];
  MathUtils.shuffleArray(choices);

  return {
    choices,
    correctIndex: choices.indexOf(correct),
    correctToken: correct
  };
}