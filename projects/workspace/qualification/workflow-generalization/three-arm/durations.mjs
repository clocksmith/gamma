// How the hours of a route are shown to every arm (clocksmith/deco#88,
// same-model three-arm test).
//
// OpenProject returns a duration as days of 24 hours and then hours: 8 hours is
// PT8H, 24 is P1D, 40 is P1DT16H. Comparing that text with "PT40H" fails. Every
// arm is therefore given the hours a route asks to write in both forms, the
// number and the application's own text, so that no arm has knowledge of the
// application's format that another lacks.

/** A whole number of hours in the form OpenProject returns. */
export function openProjectDuration(hours) {
  const days = Math.floor(hours / 24);
  const rest = hours % 24;
  return `P${days ? `${days}D` : ''}${rest || !days ? `T${rest}H` : ''}`;
}

/** The route as an arm sees it: the hours as a number and as the application writes them. */
export const withDuration = route => ({ ...route, workDuration: openProjectDuration(route.workHours) });

/** The same, in a sentence. */
export const hoursPhrase = hours => `${hours} hours (the application writes this duration as ${openProjectDuration(hours)})`;
