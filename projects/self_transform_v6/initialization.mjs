import { initialize as initializeLearned } from '../self_transform_v5/initialization.mjs';
import { counter, evaluate, mean, propose, tasks } from './experiment.mjs';
export function calibrate(protocol, seed, phi) {
  const budget=counter(), candidates=[];
  const support=Array.from({length:protocol.trainingGenerations},(_,i)=>
    tasks(seed+protocol.seedOffsets.rateSupport+i,protocol.trainSupportCount));
  const query=Array.from({length:protocol.trainingGenerations},(_,i)=>
    tasks(seed+protocol.seedOffsets.rateQuery+i,protocol.trainQueryCount));
  for(const rate of protocol.rateCandidates) {
    let child=[...phi];
    const parentLosses=[],childLosses=[];
    for(let generation=0;generation<protocol.trainingGenerations;generation+=1) {
      parentLosses.push(mean(evaluate(phi,query[generation],protocol.steps,budget)));
      child=propose(child,phi,'spsa',support[generation],protocol.steps,
        seed+protocol.seedOffsets.rateProbe+generation,budget,rate);
      childLosses.push(mean(evaluate(child,query[generation],protocol.steps,budget)));
    }
    candidates.push({rate,childLosses,parentLosses,fitness:mean(childLosses)});
  }
  return {candidates,budget,selected:candidates.reduce((a,b)=>b.fitness<a.fitness?b:a)};
}
export function initialize(protocol,seed) {
  const learned=initializeLearned(protocol,seed);
  const calibrations=Object.fromEntries(protocol.initializers.map(name=>
    [name,calibrate(protocol,seed,learned.initial[name].phi)]));
  return {...learned,calibrations};
}
