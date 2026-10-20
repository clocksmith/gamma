function findItinerary(tickets) {
  const destinations = new Map();
  for (const [from, to] of tickets) {
    if (!destinations.has(from)) destinations.set(from, []);
    destinations.get(from).push(to);
  }
  for (const flights of destinations.values()) {
    flights.sort().reverse();
  }

  const stack = ['JFK'];
  const route = [];
  while (stack.length > 0) {
    const current = stack[stack.length - 1];
    const outgoing = destinations.get(current);
    if (outgoing && outgoing.length > 0) {
      stack.push(outgoing.pop());
    } else {
      route.push(stack.pop());
    }
  }
  route.reverse();
  return route;
}
