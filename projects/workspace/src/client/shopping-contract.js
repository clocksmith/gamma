// Shopping decisions use current facts. A learned navigation trace never selects a product.
import { canonicalJson, sha256Hex } from '../journal.js';

export const quoteHash = quote => sha256Hex(canonicalJson(quote));
const integer = value => Number.isSafeInteger(value) && value >= 0;
export function validateShoppingRequest(request) {
  if (!request || !['monitor', 'computer'].includes(request.category)
    || !integer(request.maxTotalCents) || request.maxTotalCents === 0
    || !Number.isSafeInteger(request.quantity) || request.quantity < 1 || request.quantity > 10
    || !request.minimums || !Object.keys(request.minimums).length
    || Object.entries(request.minimums).some(([key, value]) => !['memoryGb', 'storageGb', 'widthPx', 'heightPx', 'refreshHz'].includes(key) || !integer(value))
    || ['query', 'accountId', 'recipient', 'address', 'postalCode', 'shipping'].some(key => typeof request[key] !== 'string' || !request[key].trim())) {
    throw Error('Incomplete shopping requirements');
  }
  return request;
}
export function eligibleOffer(offer, request) {
  return offer && typeof offer.sku === 'string' && offer.sku && offer.category === request.category
    && integer(offer.stock) && offer.stock >= request.quantity
    && integer(offer.unitCents) && integer(offer.shippingCents) && integer(offer.taxCents)
    && offer.unitCents * request.quantity + offer.shippingCents + offer.taxCents <= request.maxTotalCents
    && Object.entries(request.minimums).every(([key, value]) => integer(offer.specs?.[key]) && offer.specs[key] >= value);
}
export function selectShoppingOffer(offers, request) {
  validateShoppingRequest(request);
  if (!Array.isArray(offers) || new Set(offers.map(offer => offer.sku)).size !== offers.length) throw Error('Ambiguous product identities');
  const candidates = offers.filter(offer => eligibleOffer(offer, request));
  candidates.sort((a, b) => (a.unitCents * request.quantity + a.shippingCents + a.taxCents)
    - (b.unitCents * request.quantity + b.shippingCents + b.taxCents) || (a.sku < b.sku ? -1 : a.sku > b.sku ? 1 : 0));
  if (!candidates.length) throw Error('No in-stock product satisfies the requirements and total budget');
  return structuredClone(candidates[0]);
}
export function verifyShoppingQuote(quote, offer, request) {
  validateShoppingRequest(request);
  if (!eligibleOffer(offer, request)) throw Error('Selected product is no longer eligible');
  const expected = { sku: offer.sku, category: offer.category, specs: offer.specs,
    unitCents: offer.unitCents, shippingCents: offer.shippingCents, taxCents: offer.taxCents,
    totalCents: offer.unitCents * request.quantity + offer.shippingCents + offer.taxCents,
    quantity: request.quantity, accountId: request.accountId, recipient: request.recipient,
    address: request.address, postalCode: request.postalCode, shipping: request.shipping };
  if (!quote || canonicalJson(quote) !== canonicalJson(expected)) throw Error('Checkout differs from the verified product, price, account or delivery');
  return quoteHash(quote);
}
export function verifyShoppingReceipt(receipt, attempt) {
  return !!receipt && receipt.operationId === attempt.operationId && typeof receipt.orderId === 'string' && receipt.orderId.length > 0
    && receipt.quote !== null && typeof receipt.quote === 'object'
    && quoteHash(receipt.quote) === attempt.quoteHash;
}
