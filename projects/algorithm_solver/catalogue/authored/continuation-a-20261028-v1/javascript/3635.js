function solve(landStartTime, landDuration, waterStartTime, waterDuration) {
  let landFinish = Infinity, waterFinish = Infinity;
  for (let i = 0; i < landStartTime.length; i++) landFinish = Math.min(landFinish, landStartTime[i] + landDuration[i]);
  for (let i = 0; i < waterStartTime.length; i++) waterFinish = Math.min(waterFinish, waterStartTime[i] + waterDuration[i]);
  let answer = Infinity;
  for (let i = 0; i < landStartTime.length; i++) answer = Math.min(answer, Math.max(waterFinish, landStartTime[i]) + landDuration[i]);
  for (let i = 0; i < waterStartTime.length; i++) answer = Math.min(answer, Math.max(landFinish, waterStartTime[i]) + waterDuration[i]);
  return answer;
}

var earliestFinishTime = solve;
module.exports = solve;
