// Fawn workspace — owner session for workflow adapters
//
// Binds one owner's credential and generation to the service API. Holds no authority of its
// own: every mutation is still admitted and dispatched by the service.

const REGIONS_SCOPE = 'regions';

/**
 * @param {import('../service.js').WorkspaceService} service
 * @param {{workspaceId: string, ownerId: string, ownerGeneration: number, ownerCredential: string}} owner
 * @param {{observationRegions?: string[]}} [options] regions the owner's decisions depend on;
 *   actions bind to them whenever the cited observation recorded every one.
 */
function createOwnerSession(service, owner, { observationRegions = [] } = {}) {
  const identity = Object.freeze({
    workspaceId: owner.workspaceId,
    ownerId: owner.ownerId,
    ownerGeneration: owner.ownerGeneration,
    ownerCredential: owner.ownerCredential,
  });
  const scopeFor = (observation) => (observationRegions.length > 0
    && observationRegions.every((selector) => observation.regions?.[selector])
    ? { kind: REGIONS_SCOPE, selectors: observationRegions }
    : undefined);
  return Object.freeze({
    identity,
    observe: () => service.observe(observationRegions.length > 0 ? { ...identity, regions: observationRegions } : identity),
    submit: (observation, spec) => service.submitAction({
      ...identity,
      observationVersion: observation.observationVersion,
      observationScope: scopeFor(observation),
      ...spec,
    }),
    async act(observation, spec) {
      const admitted = await this.submit(observation, spec);
      return admitted.result;
    },
    acknowledge: (actionId) => service.acknowledge({ ...identity, actionId }),
    reconcile: (spec) => service.reconcile({ ...identity, ...spec }),
    outstanding: () => service.outstanding(identity),
    action: (actionId) => service.action({ ...identity, actionId }),
  });
}

function findElement(observation, predicate, description) {
  const element = observation.elements.find(predicate);
  if (!element) throw new Error(`observation ${observation.observationVersion}: no element ${description}`);
  return { selector: element.selector, digest: element.digest };
}

export { createOwnerSession, findElement };
