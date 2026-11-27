// Named diagnostic policies. They do not alter the default roster or game rules.
import { createPlayerPolicy } from '../../lab/policies/policy-factory.js';
import { validateDecisionResponse } from '../../lab/contracts/decision-contract.js';

export const plans = Object.freeze({
  authored: null,
  immediate: { immediate: 1 },
  compute: { immediate: 1, production: 3, power: 2, futurePower: 2 },
  power: { immediate: 1, production: 1, power: 5, futurePower: 4 },
  control: { immediate: 1, control: 5, denial: 1 },
  partners: { immediate: 1, production: 1, power: 2, partners: 5 },
  denial: { immediate: 1, production: 1, power: 1, denial: 6, control: 2 },
  refusal: { immediate: 1, refuseLeader: true },
  mixed: { immediate: 1, production: 2, power: 2, futurePower: 1, partners: 2, control: 2, denial: 2 }
});

export const distance = (a, b) => Math.max(Math.abs(a.q - b.q), Math.abs(a.r - b.r), Math.abs(a.q + a.r - b.q - b.r));
const computeYield = tile => tile.category === 'cloud' ? 2 : ['research', 'chip'].includes(tile.category) || tile.tileId.startsWith('grid_reactor-') ? 1 : 0;
const runwayYield = tile => tile.category === 'capital' ? 2 : ['consumer', 'chip'].includes(tile.category) ? 1 : 0;

// Preserve the ordinary policy's choice of action, action mode, project type,
// recruitment count and trade. Only location, host, partner and Agent change.
export function bundle(decision) {
  const p = decision.parameters || {};
  return JSON.stringify([decision.actionId, p.mode ?? null, p.buildMode ?? null,
    Boolean(p.facility), p.project?.id ?? null, p.project?.sourceId ?? null,
    p.count ?? null, Boolean(decision.consequences?.noEffect)]);
}

export function publicPower(board, owner) {
  const tile = id => board.find(t => t.tileId === id);
  const sources = [...owner.generators, ...owner.projects.filter(p => p.projectId === 'fusion_demonstrator')
    .map(p => owner.facilities.find(f => f.id === p.hostId)).filter(Boolean)];
  return new Set(owner.facilities.filter((f, i) => i === 0 || sources.some(source =>
    tile(source.tileId) && tile(f.tileId) && distance(tile(source.tileId), tile(f.tileId)) <= 1)).map(f => f.id));
}

export function spatialFeatures(packet, decision, targetSeat = null) {
  const { board, publicTable, round } = packet.observation;
  const p = decision.parameters || {};
  const tile = id => board.find(t => t.tileId === id);
  const destination = tile(p.destinationId);
  if (!destination) return null;
  const original = publicTable.players.find(owner => owner.seat === packet.seat);
  const own = structuredClone(original);
  const beforePower = publicPower(board, own);
  const beforeProduction = own.facilities.filter(f => beforePower.has(f.id))
    .reduce((s, f) => s + computeYield(tile(f.tileId)) + .5 * runwayYield(tile(f.tileId)), 0);
  const moving = own.pieces.find(piece => piece.id === p.pieceId);
  if (moving) moving.tileId = destination.tileId;
  if (p.facility) own.facilities.push({ id: `study-preview-${own.facilities.length + 1}`, tileId: destination.tileId, category: destination.category });
  if (p.mode === 'relocate') own.facilities.find(f => f.id === p.facilityId).tileId = p.facilityDestinationId;
  if (p.project?.id === 'generator') own.generators.push({ tileId: destination.tileId });
  if (p.project?.id === 'fusion_demonstrator') own.projects.push({ projectId: p.project.id, hostId: p.project.hostId });
  const afterPower = publicPower(board, own);
  const afterProduction = own.facilities.filter(f => afterPower.has(f.id))
    .reduce((s, f) => s + computeYield(tile(f.tileId)) + .5 * runwayYield(tile(f.tileId)), 0);
  const power = afterPower.size - beforePower.size;
  const energy = board.filter(t => t.category === 'energy' && t.components.filter(c => c.type === 'generator').length < 3);
  const futurePower = own.generators.length ? 0 : Math.max(0, ...energy.map(source =>
    own.facilities.filter(f => !afterPower.has(f.id) && distance(source, tile(f.tileId)) <= 1).length +
    (distance(source, destination) <= 1 ? .25 : 0)));
  const presence = (owner, district) => [...owner.pieces, ...owner.facilities].filter(c => c.tileId === district.tileId).length;
  const controlCount = owner => board.filter(t => t.category !== 'frontier' && presence(owner, t) >
    Math.max(0, ...publicTable.players.filter(r => r.seat !== packet.seat).map(r => presence(r, t)))).length;
  const control = controlCount(own) - controlCount(original);
  let partners = 0;
  let denial = 0;
  for (const rival of publicTable.players.filter(r => r.seat !== packet.seat)) {
    const rivalPower = publicPower(board, rival);
    for (const f of own.facilities.filter(f => afterPower.has(f.id))) {
      for (const r of rival.facilities.filter(r => rivalPower.has(r.id))) if (distance(tile(f.tileId), tile(r.tileId)) === 1) partners++;
    }
    if (targetSeat !== null && rival.seat !== targetSeat) continue;
    if (p.facility && destination.facilitySpacesOpen === 1) {
      const sources = [...rival.generators, ...rival.projects.filter(x => x.projectId === 'fusion_demonstrator')
        .map(x => rival.facilities.find(f => f.id === x.hostId)).filter(Boolean)];
      if (!rival.facilities.length || sources.some(s => distance(tile(s.tileId), destination) <= 1)) denial += computeYield(destination) + .5 * runwayYield(destination) + .5;
    }
    if (p.project?.id === 'generator' && destination.components.filter(c => c.type === 'generator').length === 2 && !rival.generators.length) {
      denial += rival.facilities.filter(f => !rivalPower.has(f.id) && distance(destination, tile(f.tileId)) <= 1).length;
    }
  }
  // Fixed heuristic resource values, not an oracle for actual future income.
  const effects = decision.consequences || {};
  let immediate = Number(p.actualRunway ?? effects.runway ?? 0) * .5 +
    Number(p.actualComputeCost === undefined ? effects.compute ?? 0 : -p.actualComputeCost) * .5 +
    Number(effects.trust ?? 0) * .8 - Number(effects.scrutiny ?? 0) * .5;
  if (decision.actionId === 'research' && destination.category === 'research') immediate += 1;
  if (decision.actionId === 'deploy' && destination.category === 'consumer') immediate += 1;
  if (decision.actionId === 'influence' && p.mode === 'joint_venture') {
    const rival = publicTable.players.find(r => r.seat === p.targetSeat);
    const host = rival.facilities.find(f => f.id === p.rightFacilityId);
    immediate += publicPower(board, rival).has(host.id) && afterPower.has(p.leftFacilityId) ? 2 : 0;
  }
  return { immediate, production: (afterProduction - beforeProduction) * (5 - round), power, futurePower, control, partners, denial };
}

export function rankLocations(packet, candidates, plan, targetSeat = null) {
  if (!plans[plan]) throw new Error(`Unknown spatial plan: ${plan}`);
  return candidates.map(decision => {
    const features = spatialFeatures(packet, decision, targetSeat);
    const weight = Object.entries(plans[plan]).reduce((sum, [key, value]) => sum + value * (features?.[key] || 0), 0);
    return { decision, features, weight };
  }).sort((a, b) => b.weight - a.weight || a.decision.decisionId.localeCompare(b.decision.decisionId));
}

export class SpatialStudyPolicy {
  constructor(profile, backend, { plan = 'authored', scaffold = false, targetSeat = null, rosterProfileIds = [], force = null, observe = null } = {}) {
    if (!(plan in plans)) throw new Error(`Unknown spatial plan: ${plan}`);
    this.base = createPlayerPolicy(profile, backend, { policyTreatment: scaffold ? 'infrastructure_plan_v1' : null, rosterProfileIds });
    Object.assign(this, { plan, targetSeat, force, observe });
    this.decisions = 0; this.changed = 0; this.locationDecisions = 0;
  }
  async decide(packet) {
    const ordinary = await this.base.decide(packet);
    let chosen = packet.legalDecisions.find(d => d.decisionId === ordinary.decision.decisionId);
    const offer = packet.observation.publicTable.pendingJointVenture;
    if (plans[this.plan]?.refuseLeader && offer) {
      const proposer = packet.observation.publicTable.players.find(p => p.seat === offer.proposerSeat);
      if (proposer.currentScore > packet.observation.self.currentScore) {
        chosen = packet.legalDecisions.find(d => d.decisionId === 'agreement_reject') || chosen;
      }
    }
    const candidates = chosen.parameters?.destinationId ? packet.legalDecisions.filter(d =>
      d.parameters?.destinationId && bundle(d) === bundle(chosen)) : [];
    const ranked = this.plan === 'authored' || !candidates.length ? [] : rankLocations(packet, candidates, this.plan, this.targetSeat);
    if (ranked.length) chosen = ranked[0].decision;
    const forced = this.force?.(packet, chosen, candidates);
    if (forced) {
      if (!candidates.some(d => d.decisionId === forced.decisionId)) throw new Error('Forced branch changes its action bundle or selects an illegal placement');
      chosen = forced;
    }
    this.decisions++;
    if (new Set(candidates.map(d => d.parameters.destinationId)).size > 1) this.locationDecisions++;
    if (chosen.decisionId !== ordinary.decision.decisionId) this.changed++;
    this.observe?.({ packet, chosen, candidates, ranked });
    return { decision: validateDecisionResponse(packet, { decisionId: chosen.decisionId, rationale: `Spatial study: ${this.plan}` }),
      receipt: { ...ordinary.receipt, spatialStudyPlan: this.plan, spatialStudyScaffold: this.base.treatment, selectedDecisionId: chosen.decisionId } };
  }
}
