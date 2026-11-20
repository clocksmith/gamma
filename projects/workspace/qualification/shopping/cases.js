// Learning inputs are distinct from the twenty evaluation requests. No model or
// workflow sees the server-side oracle or fault schedule.
export function requestFor(index) {
  const monitor = index % 2 === 0;
  return { query: monitor ? `OLED monitor selection ${index}` : `Computer selection ${index}`,
    category: monitor ? 'monitor' : 'computer', minimums: monitor ? { widthPx: 3840, heightPx: 2160, refreshHz: 120 }
      : { memoryGb: 32, storageGb: 1024 }, maxTotalCents: 200000 + index * 100, quantity: 1,
    accountId: 'test-shopper', recipient: `Test Shopper ${index}`, address: `${100 + index} Example Street`,
    postalCode: String(10000 + index), shipping: 'Standard' };
}
export function catalogFor(index) {
  const request = requestFor(index), prefix = request.category === 'monitor' ? 'DISPLAY' : 'COMPUTER';
  const make = (suffix, unitCents, specs, stock = 4) => ({ sku: `${prefix}-${index}-${suffix}`, category: request.category,
    unitCents, shippingCents: 1800, taxCents: 9000, stock, specs });
  const bad = { ...request.minimums, [Object.keys(request.minimums)[0]]: 1 };
  return [make('DECOY', 30000, bad), make('B', 110000 + index * 100, request.minimums),
    make('A', 110000 + index * 100, request.minimums), make('SOLDOUT', 50000, request.minimums, 0)];
}
export function trialCases(contract, smoke = false) {
  const clean = Array.from({ length: smoke ? 2 : contract.cleanTrials }, (_, index) =>
    ({ id: `clean-${index}`, index: index % contract.heldOutRequests, fault: null, expected: 'completed' }));
  const faults = contract.faults.flatMap(fault => Array.from({ length: smoke ? 1 : contract.faultTrialsPerKind }, (_, index) => ({
    id: `${fault}-${index}`, index: index % contract.heldOutRequests, fault,
    expected: ['layout-change', 'lost-acknowledgment', 'browser-restart'].includes(fault) ? 'completed' : 'stopped',
  })));
  return [...clean, ...faults];
}
