/** Pure authority for registering a final-Era AGI claim. */
export function declarationReadiness(state, player) {
  const requirements = state.requirements;
  const result = {
    ready: false,
    failingRequirement: null,
    ppaIterations: 0,
    capacityOps: 0,
    gridReadyFacilities: 0,
    requiredGridReadyFacilities: 0,
    supportingSeats: []
  };
  const fail = (requirement) => ({
    ...result,
    failingRequirement: requirement
  });

  if (player.agiClaimed || player.agiDeclared) return fail("already_claimed");
  if (player.capability < requirements.capability) return fail("capability");
  if (player.compute < requirements.computeCost) return fail("compute");
  result.ready = true;
  return result;
}
