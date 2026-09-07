# Homepage and public-source deployment

Deployed https://canvascontext.com/ from clean source commit d68192c8, executable
0.19.14 / rules rc.16 / engine 0.22.5. The homepage puts final game materials first
and nine public source links below. Exact selected rule, component, interface and
variable source files are copied into sources/. No author bible or internal review
source is included. This is a hosted-output boundary, not repository access control.

312 tests passed before workspace sync. Comparing that tested tree with d68192c8
showed only added evidence files, with no game or homepage source delta. Content
checks and immutable release verification passed. The public package was rebuilt
after sync, then deployed using the existing Firebase hosting configuration.

Live Chrome checks at widths 1440 and 390 verified source-link placement, all 13
local homepage links, game startup, the Quantum completion display, and absence
of page errors. Author lore and internal-source URLs returned 404. The live
release identity matched the deployed package byte for byte; sampled public source
files also matched their packaged hashes. Screenshots and compressed raw logs are
retained with the full package hash manifest in verification.json.

The deployment includes Mega-Cluster II, Fusion III, Quantum IV and the complete
player rulebook organization. Quantum values remain provisional; these checks do
not establish human learning, enjoyment or gameplay balance.
