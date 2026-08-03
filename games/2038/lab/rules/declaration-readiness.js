/**
 * Pure declaration authority shared by the simulator and browser surfaces.
 * Grid readiness is demonstrated during Production and persisted on Facilities;
 * this check never re-runs Power allocation or contract resolution.
 */
export function declarationReadiness(state, player) {
  const counters = { ppaIterations: 0, capacityOps: 0 };
  const requirements = state.requirements;
  const result = {
    ready: false,
    failingRequirement: null,
    ppaIterations: 0,
    capacityOps: 0,
    gridReadyFacilities: 0,
    requiredGridReadyFacilities: requirements.facilities,
    supportingSeats: []
  };
  const fail = (requirement) => ({
    ...result,
    failingRequirement: requirement,
    ppaIterations: counters.ppaIterations,
    capacityOps: counters.capacityOps
  });

  const supportingSeats = new Set();
  for (const facility of player.facilities) {
    counters.capacityOps += 1;
    if (facility.gridReady === true) {
      result.gridReadyFacilities += 1;
      for (const seat of facility.gridReadySupportSeats || []) {
        supportingSeats.add(seat);
      }
    }
  }
  result.supportingSeats = [...supportingSeats].sort((left, right) => left - right);

  if (player.agiDeclared) return fail("already_declared");
  if (player.capability < requirements.capability) return fail("capability");
  if (player.customers < requirements.customers) return fail("customers");
  if (player.trust < requirements.trust) return fail("trust");
  if (player.compute < requirements.computeCost) return fail("compute");

  result.ppaIterations = counters.ppaIterations;
  result.capacityOps = counters.capacityOps;
  if (result.gridReadyFacilities < requirements.facilities) {
    result.failingRequirement = "grid_ready_facilities";
    return result;
  }
  result.ready = true;
  return result;
}
