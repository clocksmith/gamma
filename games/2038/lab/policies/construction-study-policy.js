// Public-observation Research/Deploy diagnostic; not an optimized default persona.
// Historical infrastructure treatments remain in their sealed releases.
export function constructionStudyScore(packet, decision, treatment) {
  if (treatment !== 'research_deploy_plan_v1') return null;
  const {self, board, round} = packet.observation;
  const p = decision.parameters || {};
  const tile = id => board.find(t => t.instanceId === id);
  const unequipped = self.pieces.some(org => !org.equipped);
  const needsEquipment = round <= 2 && unequipped && self.compute < 4;
  if (decision.consequences?.stage === 'action_selection') {
    if (!decision.consequences.resolvableWithoutTrade) return .001;
    return ({
      fund: self.runway < 2 && needsEquipment ? 100 : 1,
      build: needsEquipment && self.runway >= 2 ? 80 : .01,
      research: self.capability < 9 ? 60 : self.capability < 12 ? 20 : .01,
      deploy: self.canDeploy ? 70 : .001,
      influence: self.reputation < 4 ? 50 : self.reputation < 6 ? 25 : .01,
      organize: .1,
    })[decision.actionId] ?? null;
  }
  // Legal choices own cost and reachability. Value the Org's actual destination,
  // including a moving Org being equipped there, rather than obsolete projects.
  if (decision.actionId === 'build' && p.equipOrgId) {
    const org = self.pieces.find(o => o.id === p.equipOrgId);
    const destination = tile(org.id === p.pieceId ? p.destinationId : org.tileId);
    return 1 + (destination?.yield.resource === 'compute' ? 20 : 2) *
      (destination?.yield.amount || 0);
  }
  if (decision.actionId === 'fund' && p.destinationId)
    return p.mode === 'venture' && self.reputation > 2 ? 10 : 5;
  return null;
}
