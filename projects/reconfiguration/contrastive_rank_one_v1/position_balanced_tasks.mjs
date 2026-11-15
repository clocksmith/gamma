import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { validateTasks } from '../rotation_v1/task_contract.mjs';

// New non-code families; each semantic answer occupies every letter once.
const cases = [
 ['parcel', 'The red parcel contains a scarf. The blue parcel contains a mug. The green parcel contains a pen. The yellow parcel contains a key. What is in the green parcel?', ['scarf','mug','pen','key'], 2],
 ['nickname', 'Mara is called Finch, Oren is called Fox, Pavi is called Lynx, and Sela is called Wren. What is Pavi called?', ['Finch','Fox','Lynx','Wren'], 2],
 ['before', 'The cards are arranged left to right: cedar, maple, birch, oak. Which card is immediately to the left of birch?', ['cedar','maple','birch','oak'], 1],
 ['after', 'The stops in order are Harbor, Meadow, Quarry, Summit. Which stop comes immediately after Meadow?', ['Harbor','Meadow','Quarry','Summit'], 2],
 ['replace', 'Replace every occurrence of the letter a with o in the word banana. What is the result?', ['banono','bonana','bonono','banano'], 2],
 ['suffix', 'Remove the final three letters from the word starfish. What remains?', ['star','starf','fish','stari'], 1],
 ['constraint', 'Exactly one object is wooden. The cup is metal, the ring is stone, and the spoon is plastic. The four objects are cup, ring, spoon, and box. Which is wooden?', ['cup','ring','spoon','box'], 3],
 ['mapping', 'A codebook maps cloud to violin, river to drum, stone to flute, and leaf to harp. Decode the codeword river.', ['violin','drum','flute','harp'], 1],
];
export const fixture = {
 schema:'gamma.position-balanced-development/v1',
 questionPrefix:'Answer the question using the information provided. Choose only A, B, C, or D.',
 tasks:validateTasks(cases.flatMap(([id,body,choices,answer])=>Array.from({length:4},(_,rotation)=>{
  const rotated=choices.slice(rotation).concat(choices.slice(0,rotation));
  return [`${id}-p${rotation}`,body,rotated,(answer-rotation+4)%4];
 }))),
 baseGate:{minimumCorrect:16,maximumCorrect:30,minimumStableCases:4,maximumModalLabelCount:16},
};
if(process.argv[1] && resolve(process.argv[1])===fileURLToPath(import.meta.url)) console.log(JSON.stringify(fixture));
