export function canonicalRulesVariant(config) {
  if(config.board.layout !== 'shared-action-areas')throw new Error('Only the six-area rules are current.');
  return {kind:'six-area-four-track-v1',pausedFactionAbilities:[]};
}
export function effectiveRulesVariant(config,overlay={}) {
  if(!overlay||typeof overlay!=='object'||Array.isArray(overlay))throw new TypeError('rulesVariant must be an object');
  const current=canonicalRulesVariant(config);
  for(const key of Object.keys(overlay))if(!Object.hasOwn(current,key))throw new RangeError(`Unsupported rules option: ${key}`);
  if(overlay.kind!==undefined&&overlay.kind!==current.kind)throw new RangeError('Alternate rules modes are unavailable.');
  if(overlay.pausedFactionAbilities!==undefined&&!Array.isArray(overlay.pausedFactionAbilities))throw new TypeError('pausedFactionAbilities must be an array');
  return {...current,...structuredClone(overlay)};
}
