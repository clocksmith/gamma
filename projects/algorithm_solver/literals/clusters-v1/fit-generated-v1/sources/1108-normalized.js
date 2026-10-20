function defangIpv4Text(addressText) {
  return addressText.split('.').join('[.]');
}
function solve(address) {
  return defangIpv4Text(address);
}
