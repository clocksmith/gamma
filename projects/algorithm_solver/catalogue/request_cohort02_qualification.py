"""Fixed 42-problem ordinary qualification preparation through the existing runner.

No new engine or registry. Exact pre-source/oracle evidence and both original
source reviews remain immutable; post-source interface approval is separate.
"""
from __future__ import annotations
import argparse
import os
import stat
from datetime import datetime, timezone
from pathlib import Path
from . import imported_qualification as q
from . import request_git_queue05_subset02_oracles as q05s02
from . import request_git_queue06_oracles as q06s01
from . import request_git_queue06_subset02_oracles as q06s02
from . import request_git_queue06_subset03_oracles as q06s03
from . import request_git_queue07_oracles as q07s01
from . import request_git_queue08_subset01_oracles as q08s01
from . import request_git_queue08_subset02_oracles as q08s02
from . import request_git_queue08_subset03_oracles as q08s03
from .gated_payload_read import read_payload
from .known_spec_service import KnownSpecService, _boundary_snapshot

IDS = (2585,
 2654,
 2662,
 2698,
 2712,
 2718,
 2730,
 2746,
 2750,
 2768,
 2769,
 2771,
 2786,
 2789,
 2791,
 2798,
 2800,
 2812,
 2830,
 2844,
 2857,
 2865,
 2899,
 2909,
 2924,
 2957,
 2981,
 2998,
 3002,
 3006,
 3012,
 3016,
 3020,
 3039,
 3048,
 3070,
 3080,
 3081,
 3085,
 3096,
 3101,
 3106)

LANGUAGES = ('javascript', 'python')

DOMAIN = 'request-cohort02-v1'
# New-domain mutable host evidence only; excluded from immutable payload/code pins.
MUTABLE_ACCESS_LOG = 'payload-acquisition.jsonl'
MAX_ACCESS_LOG_BYTES = 8 * 1024**2

SOURCE_GROUPS = {'q05s02': (2585, 2654, 2662, 2698, 2712),
 'q06s01': (2718, 2730, 2746, 2750, 2768, 2769),
 'q06s02': (2771, 2786, 2789, 2791, 2798, 2800),
 'q06s03': (2812, 2830, 2844, 2857),
 'q07s01': (2865, 2899, 2909, 2924, 2957),
 'q08s01': (2981, 2998, 3002, 3006, 3012, 3016),
 'q08s02': (3020, 3039, 3048, 3070, 3080),
 'q08s03': (3081, 3085, 3096, 3101, 3106)}

BINDINGS = {2585: {'batch_count': 68,
        'batches_sha256': '38be7558b2b869b480cfa4e34c59e2b02ad62c311b2d3c1db2bcbac5263e8209',
        'case_count': 2152,
        'cases_sha256': '6361c5a5c260de8815c12dc0b573743641debf8683645309e738b03664bc4553',
        'categories_sha256': '305594b89fae7456f9557d613b3caed376480a0ac2ca85997f19a6507514cffb',
        'git_blob_oid': {'javascript': '87fb74086ea9fa97ba6b90b3228511ca8b04dec3',
                         'python': '5a49dcc4d433d2d85ae15ee9c6c2edea9e2fe2b3'},
        'oracle_group': 'q05s02',
        'parameters': ['target', 'types'],
        'source_bytes': {'javascript': 603, 'python': 408},
        'source_sha256': {'javascript': 'bc90b018624f162361aeb1faa97bcc94bfb5904ed506938909690df9cf98e562',
                          'python': '060a8cf0d41050b6bccc5551b24beb9291bcc723739700cb89969189d6be3c21'},
        'statement_sha256': 'fe38a80f98e3d88be276a1b454794ad0fb1d7fa507617273f2fabaa6069f072d'},
 2654: {'batch_count': 14,
        'batches_sha256': 'cfdfff68d24c4f49f3e08b256ff17dc64482d8aa4050ee2e995fb9c0fb60b952',
        'case_count': 440,
        'cases_sha256': 'e1bb1fafc3eb58f9d872c984c4c3db04072b4e05ee78348eef90564986fa885f',
        'categories_sha256': '4b56df43cee0c25a7320cbcb63700d9a861579d7a493d1b936fab11d5b85d57a',
        'git_blob_oid': {'javascript': '6b3d7f961492b4382bea379223de7271b9f00429',
                         'python': 'a1d88ac22b24073cad86ddc791a4942da12ba948'},
        'oracle_group': 'q05s02',
        'parameters': ['nums'],
        'source_bytes': {'javascript': 469, 'python': 428},
        'source_sha256': {'javascript': 'a46f18979c7b6379653e9626676f44f200032800d42722a7020bf39b85a8670c',
                          'python': '15746a0c82488ac2e328c7bbf3f1c00e98b52edd1accb2f620813bfcd0be5c8b'},
        'statement_sha256': '20e800d553bf1e250a7aaf843537f3b930b5e7a29a2ad3cefaef5294b47c35db'},
 2662: {'batch_count': 77,
        'batches_sha256': '41831e2247fd86ad30ec7bc64d57079e08bb63c5020e9887787662b9308161e7',
        'case_count': 2440,
        'cases_sha256': '1360ca001349a6aa6975b608e81cd04e0d7926f303e846e6523abddf21a45e41',
        'categories_sha256': 'ab2d46e20e68c6718796aa350bbe232add37d9e04437aaa9683122dd68fd01e1',
        'git_blob_oid': {'javascript': 'af39d98bd3c8545f114715acbda6a7dc3fd98766',
                         'python': 'a94742350a75107d1e28357e48fa7a095763d316'},
        'oracle_group': 'q05s02',
        'parameters': ['start', 'target', 'specialRoads'],
        'source_bytes': {'javascript': 676, 'python': 628},
        'source_sha256': {'javascript': 'c45f5b7ab9fa4bfa5e33fc3991099ad0a12162434bcd9a1947d67b32fccf3019',
                          'python': '62fdd4cbfa5c99fe2a82bb6e5ea6245730c7fc91ee9f360e3ca688a3e089baf4'},
        'statement_sha256': '8aaccd625a57eea8e05784bcb49681e43029f43288f94b8eb3cb8ade2ac4e194'},
 2698: {'batch_count': 32,
        'batches_sha256': 'a0fc18ba794f6d021e5e11278d646aa01529e6ca6bca80feb9acc9b24ff09fa5',
        'case_count': 1000,
        'cases_sha256': '84b9e1882f9ec993fcc834d3dc4e0248058a8b59f601b39b4aa784746557194d',
        'categories_sha256': 'a3eb7893fe0ed5ecdd85b9cb0dcda5aab8d837799b92f6b49e3df174fd3f2202',
        'git_blob_oid': {'javascript': '2d9b28a493c9d2004c0e0e1b1b254a9ef3a83328',
                         'python': 'a061a70fa0d934da7f4aab7cce725c4c82c3b8c4'},
        'oracle_group': 'q05s02',
        'parameters': ['n'],
        'source_bytes': {'javascript': 413, 'python': 529},
        'source_sha256': {'javascript': 'f830ac217db231bd310be5b5e5aaa4195ecb021c5557de73eed3f46e491bd41f',
                          'python': 'dfc1c4541495e391073dac1b46191d8a35ec66c5bedccbfef5eff2f84b2db532'},
        'statement_sha256': '81405fc39dd74099a078a8ede3f641ea18277953d54eee2f6cdd2b4dfbd49af1'},
 2712: {'batch_count': 19,
        'batches_sha256': '05212280a7104102038ff8027ccfe14c1fd24b54081d1dcd198de65b08f32e01',
        'case_count': 593,
        'cases_sha256': '978a4fecfee649d58a54c170a02f3a905ea2cb3ea7d639f22651760dc8221d48',
        'categories_sha256': 'e1ce14489cfa468b002c92278406ef8371db752beb5b86a31391cfbd663ebb81',
        'git_blob_oid': {'javascript': 'af6deebf6a347f9f1ec223bfb0d6ec377b2a4c4d',
                         'python': '2be394bb293175bb8fe935931520bf89ee23af5d'},
        'oracle_group': 'q05s02',
        'parameters': ['s'],
        'source_bytes': {'javascript': 262, 'python': 197},
        'source_sha256': {'javascript': 'd4a32d0ef65a46a39c6905d1408910b6dbe75295a5803ae92ba5bed58cc5383e',
                          'python': '969451dfa6085a806d6d80264df4771ddaef78083c049d477b4fa88debe888bf'},
        'statement_sha256': 'c925ccad696554dfecd81e2595db657f683a783ce8188f50487f3bfb36184c70'},
 2718: {'batch_count': 25,
        'batches_sha256': '3b4ab16d27b43ace17ff5e4c9ab6cc41a74ae1a8c1c122ded941e3e1f06c3f54',
        'case_count': 733,
        'cases_sha256': '28dee149d2931e315d6c90e1392df0febdd8fc1c7b9af68017f10640ac801c89',
        'categories_sha256': '0b90f14920364a65e1c1987d12d845316aa8d1de4a77e7003f8a62bf3df9dae3',
        'git_blob_oid': {'javascript': '80113666d36b7f6cb54eb34a9955b81ecfd743af',
                         'python': 'fc3abcf35df26566e011525a928a36d67a95cc22'},
        'oracle_group': 'q06s01',
        'parameters': ['n', 'queries'],
        'source_bytes': {'javascript': 336, 'python': 300},
        'source_sha256': {'javascript': '44509298038b457e42f435e32ce507888fa0093f5bca80e4cd93d35b05461caa',
                          'python': '125311f3adea83addecfec5f653d8b7ea2bec8a0a5670f8fe73d067503f11718'},
        'statement_sha256': '72b50ec3b159cafc49e4d41dc1d208844f633a81e9dc22bcc3b102f1ed79b4b1'},
 2730: {'batch_count': 19,
        'batches_sha256': 'cc3e9d4cf75a13bfd3750ed1932031aeb5afb6b6d7a817b862d7effdfce3f696',
        'case_count': 586,
        'cases_sha256': '0d1585c1dc7c6f82029933e8818a8ac3a24606b86c2d04665ec3f960f7fa615d',
        'categories_sha256': 'a440b7feb2b825ee5925f893552d44e3b2f1e90858f732b188c61c654b3dbb92',
        'git_blob_oid': {'javascript': 'e177a468f20c7e7044f096492b46f616e522cbfc',
                         'python': '85746431ef84f3be02fed2ac43f6e21d92f5697e'},
        'oracle_group': 'q06s01',
        'parameters': ['s'],
        'source_bytes': {'javascript': 561, 'python': 558},
        'source_sha256': {'javascript': 'e0741f18588367226254b3180e9a425aaa48ef7a4e4d657887107fb0ceaeb9fe',
                          'python': '0a06f35786977fbe504b7bc4ff3fd9cd98d365e31b8fe41017956700ba64226b'},
        'statement_sha256': '39bb80d5c3df39b4936f15652e26b5056d3f141098cf70bec96f570c5b2b4c1f'},
 2746: {'batch_count': 13,
        'batches_sha256': 'af9b4e18b7d70f2867b1d6233b02e0ddf5ea63d1a7fe8da6f956426ba897afb7',
        'case_count': 405,
        'cases_sha256': '7c171d394b6fa1f5a7628d59285cdadb210208c3546c1c399f8bd94d3fa2628c',
        'categories_sha256': '1a49efada583404e83dbdb8e0fac4b6e88b259da6012e4ae1ac727583b00ade8',
        'git_blob_oid': {'javascript': '9ba58d15853f29ffd507af35043a3015c37cd5a9',
                         'python': '9f3c95185949868caf683293abdd0a7082f5506c'},
        'oracle_group': 'q06s01',
        'parameters': ['words'],
        'source_bytes': {'javascript': 597, 'python': 528},
        'source_sha256': {'javascript': 'c7f780bb3934e10b17ecaa16363288a42a0784b21e4aefd3da02de5c3a80db26',
                          'python': 'dd20595dbe3123e6ea1cb6d1194fa5f29f061e99c7299219669229a3189e4cce'},
        'statement_sha256': 'c9d8b5836086aac0af02dd3ddefb34b3f102e69d0f61b4dc0d2175f5dc41c148'},
 2750: {'batch_count': 34,
        'batches_sha256': '47816c600fe12b631c27b8e4e4c1e7617c3839445ac4bf6f777954983de10d91',
        'case_count': 1065,
        'cases_sha256': 'd983647994cc69df60bef76c5cd72546978460ac7286ba657f6d1cefb08d8481',
        'categories_sha256': '250ec62f7e793f62fd8c3ebce7e8fbf5e84d2470cbae974197694fd9ec6ba03f',
        'git_blob_oid': {'javascript': 'a84133aab6c2e47790f70021b3236e7362a2f154',
                         'python': 'f6ab8a208e8615fb2fef1831e2e0926a5f20b1c2'},
        'oracle_group': 'q06s01',
        'parameters': ['nums'],
        'source_bytes': {'javascript': 292, 'python': 299},
        'source_sha256': {'javascript': 'fe1fc981564eee2140f23b9827475f4382247aa1455d044049ee948998b074a2',
                          'python': '0deacb6fb520ec8925391265251007e75dbe8868b983cfb548a040d43110e42e'},
        'statement_sha256': 'df44cdee887473e477c3c23d027f34978936de9a42b0be1a8f74ac9600998f9b'},
 2768: {'batch_count': 23,
        'batches_sha256': 'a9d126d6a94265533395b40793010341b7ac9a81cc3e13aa87fb66e4cbfe2291',
        'case_count': 712,
        'cases_sha256': '744bef7f694c5130fa2dca0088256cd76ff26b5dc640400b0727d49a51b709ca',
        'categories_sha256': '2cc9b557d45c4dba5615332e65a8becc91057630332410d7d226c4d598cae824',
        'git_blob_oid': {'javascript': '7bfaa5c4761fbe44c15c7e8e6da94c025569233f',
                         'python': '4a32f8f5ead141d022e7538489e7464ae3af327b'},
        'oracle_group': 'q06s01',
        'parameters': ['m', 'n', 'coordinates'],
        'source_bytes': {'javascript': 419, 'python': 408},
        'source_sha256': {'javascript': 'ab4774f88ac81f2dda42e15134a0a31ad4affc093e0b7489ea7a4b119f141f99',
                          'python': 'f53e8ec1fb037d7b0b52602abc15c0d0b0de769729fa5c9188af11676ab1d0d9'},
        'statement_sha256': 'f49b980149ccd1dfada38e117923aea3c8b2888b173564cf3953ead0086834a9'},
 2769: {'batch_count': 79,
        'batches_sha256': '08fcf42ab61719806fc2e83c8120583bc89b4f4fbcfc8ac3de94defd443981e0',
        'case_count': 2500,
        'cases_sha256': 'b1590cf40c2474f48c2dcf1799971a09c24469b375b96b3eaad3ea194c018374',
        'categories_sha256': '63bc1b29a5cb364366a06b9dbd7730d31ceb703e6bf7e22ac0b19752338e8c58',
        'git_blob_oid': {'javascript': '8f33bf09ba71d0898ccb0a6bfcfcc0a36c83daef',
                         'python': '5897a78ce4aa478bf31a5207f5064aacbb7cc991'},
        'oracle_group': 'q06s01',
        'parameters': ['num', 't'],
        'source_bytes': {'javascript': 191, 'python': 153},
        'source_sha256': {'javascript': '918dc77a6b13fa0377f74f059d4301ea10c3d424e12566b59dadc88133f0b9e8',
                          'python': '6b6a0573e92eb2c21a4fb51945bff9ea750ba99fa6b047e8dede6ed55fedf2c0'},
        'statement_sha256': '9db3593b06fb5c026256d172fde27fd354b40e2cb8986e8d96ae5a8574edf685'},
 2771: {'batch_count': 14,
        'batches_sha256': 'deddd7dade3488c6e6cb714f913a2800e47d1a27a6fc37e5ca3a13599523534e',
        'case_count': 409,
        'cases_sha256': 'f3df3111252df46e7ab0ef6367e93986e666f82ee0ee74f8d4c0cc307fb55ad7',
        'categories_sha256': 'bf31aab3204dd900068a36f5e027ab9e145c509b6d21976951dbb8991de7c9e2',
        'git_blob_oid': {'javascript': '65682ec592cedd39f01219fce6515dc2e00549e1',
                         'python': '1b79304dc7ad7c5a7af4d86105aa7aa92c5a8c47'},
        'oracle_group': 'q06s02',
        'parameters': ['nums1', 'nums2'],
        'source_bytes': {'javascript': 408, 'python': 438},
        'source_sha256': {'javascript': '5146cd6c3ca7140ca75be6d9d0c350c02a607d0a5f46b01dbc21f4e8eaa5859e',
                          'python': '9935f33d93dbb606d5936301bb6bd6b4fde39ae0bb6790b165343bd10b5c362f'},
        'statement_sha256': 'cc9a1769cfab778b654a57473b6c078e96b25a3c9023c553810f0708aee19959'},
 2786: {'batch_count': 37,
        'batches_sha256': 'bdcb3bdf72bc4567f1220f5f9256e57f75b5f5ebaee3224a22f956bf89b32e1b',
        'case_count': 1145,
        'cases_sha256': '4ae42b359cb26c17ff99777c735dc3486d758cde54d242d3b0d965189b8eafd4',
        'categories_sha256': 'a9bb85df9e1160cc857dca611279f56dc97bdb65be3dd0fedf964fe48238a283',
        'git_blob_oid': {'javascript': 'ab11fdef3d1dcefe36eafd2bf79c8d1e92ab928a',
                         'python': 'fcfdcf7a18296a82e459c253d8abd057617ac03b'},
        'oracle_group': 'q06s02',
        'parameters': ['nums', 'x'],
        'source_bytes': {'javascript': 358, 'python': 296},
        'source_sha256': {'javascript': 'd869f3292457e5fcc5c169858308cc270d9c3220233fac79e0cfc502a859185b',
                          'python': 'b3260cbbd478e35871b2a9f32b7cf82692ac1e3351df907eee4f07e20e66bb61'},
        'statement_sha256': '9f6649dc5d5fcf13a264ad1dea098b4ab9ae3925cac1302b58b2e91dda15dcd0'},
 2789: {'batch_count': 38,
        'batches_sha256': 'afd2225e825b5f3ff466d1b0e2607c76c3b6d36f0ea3a72789eeab7d6a75f521',
        'case_count': 1168,
        'cases_sha256': 'ff97c58ae990033722e3825731902076418a5d2b849c877e92dc74999d8f9151',
        'categories_sha256': 'edb636cc9fd08542ef9ad3e02ff1d2066e6ce75361d068980fe44ff63630b065',
        'git_blob_oid': {'javascript': 'b386f9956cf5061085230dcc1bd87c0a0000c47a',
                         'python': '277613f1d8331fd5d82c2868d7c5f343b6d7d1c8'},
        'oracle_group': 'q06s02',
        'parameters': ['nums'],
        'source_bytes': {'javascript': 305, 'python': 266},
        'source_sha256': {'javascript': 'd3c89f88c2f6b59e6713a01cc7cc166f79c7ea573fa70991d0df339f51c4496d',
                          'python': 'f64762a183b46ee71fd7f24f6dc51924a2afe5e50e21b03b2b824fb89ce8ec0d'},
        'statement_sha256': '8dc3f771a572163719ed432d8bccf7cbfcd1d06e7ac67ce81a689251f92e5b7b'},
 2791: {'batch_count': 32,
        'batches_sha256': 'c2c3671757b6fbb2be721ccefa8f0ee5c81e6d39d4f50b41e54ba1c7903b828d',
        'case_count': 970,
        'cases_sha256': '946301fda9a75bbe8e7653c7433477586f590775bc48f0850dc35d40de750e55',
        'categories_sha256': 'ba4f62797b7a2d6162735de62c61494a5932c75cdc38d274e3019ce6d6c399b3',
        'git_blob_oid': {'javascript': '64d0a40697ef9ceaaeaa1685117ef4a259370086',
                         'python': '437e64113e57789bd43a5a43c54ee67b5658c387'},
        'oracle_group': 'q06s02',
        'parameters': ['parent', 's'],
        'source_bytes': {'javascript': 798, 'python': 762},
        'source_sha256': {'javascript': 'f4f29323fa852007612f7b35923b73dd6ce40b03f36ca0c17d9c37ed3f14c8de',
                          'python': '77488e3b2c8b8d51b8d035be8bc5e847f947ecd8a0a76d53cf12288a1eaaf855'},
        'statement_sha256': '1a1a57d9d1bd1c1109a80ef74b54e4728e365a3d42a72655a7fc98461f9c202b'},
 2798: {'batch_count': 22,
        'batches_sha256': '2edf9fe823d7325d7052e4b01b6f5b91c6d1a85c1fb0dda741cd8345992e306d',
        'case_count': 678,
        'cases_sha256': 'e5e64d92e8d0bb01fb354410b5ef32c5d2247479da7bc7268e66da735082e99a',
        'categories_sha256': 'c5b0b767fc7d11c4f7f823194eb808748105aa2f95a46321511d910dc789ff29',
        'git_blob_oid': {'javascript': 'b08babbb7091bd84fbc9f7ee6659d6dba45d5782',
                         'python': 'f72e0359b1175b2a66bd6eefb4cb62ea3f67bee5'},
        'oracle_group': 'q06s02',
        'parameters': ['hours', 'target'],
        'source_bytes': {'javascript': 221, 'python': 168},
        'source_sha256': {'javascript': 'd2c68b66fabbbcdbba179286ef25f2a5223da6e5fa497a2982ff63d2a6e8887e',
                          'python': '3bd0596310e1fff70b1533ad25d92c7d4d955b1386a07fb2c3ed23f341502512'},
        'statement_sha256': 'b327a2e9eb686d291600c7aa6f0f395ab0e6dc75b83c6f016ab132bb1905f00c'},
 2800: {'batch_count': 10,
        'batches_sha256': 'c503b3f53d408667c302cb70f9f9c0d8a0cc18b40a7239865470585c2004afbb',
        'case_count': 293,
        'cases_sha256': 'e13ec7c279f97d673275fb8b4f8a4182add65967756fe0893e6e181aa5509c67',
        'categories_sha256': '5680328e79a347c392e9bbc66eb03bcff3af56424f74307dd84f6acd2e037a2e',
        'git_blob_oid': {'javascript': '63688f8e89f4951a4912dc7eff15f7e1f484b5a2',
                         'python': '7ae69ca32d923d01482565f8b9cccce6e74cae5c'},
        'oracle_group': 'q06s02',
        'parameters': ['a', 'b', 'c'],
        'source_bytes': {'javascript': 539, 'python': 484},
        'source_sha256': {'javascript': '59c3c1645efc9b8a9ad539aab0bddbc7dc64884b542a22f628e67821ce71f672',
                          'python': '6a0f7a7456a307d0fcd3685740f42aab57fefef4e632e6700821b0d784c2ed9b'},
        'statement_sha256': 'efba90f4862b3c6aa5519804c10300859671ad4aa3a4e3c9ac77c5f331612a90'},
 2812: {'batch_count': 21,
        'batches_sha256': '1863f8c8935353954a9355b407808c36faaaa7b945ccf1c4fd4cdaabfed5f487',
        'case_count': 613,
        'cases_sha256': 'f70df107a860be03e5f30f0236569e06e902db1c8c3f797aabd3d916d530b603',
        'categories_sha256': '911bc24dc079ca275047e9af31911ea3570f220c117ccf7465ae8cee2fabf816',
        'git_blob_oid': {'javascript': '29bb15630e1c924c25453426fd3acb91aef2d8c1',
                         'python': '3e6b59faa447e836dd588f2a74ed21fffb4c5aa2'},
        'oracle_group': 'q06s03',
        'parameters': ['grid'],
        'source_bytes': {'javascript': 908, 'python': 1036},
        'source_sha256': {'javascript': '34ba75f2e37323ef1412543c04e8ef47318413be85da7ff356156f8b173906f2',
                          'python': 'bea543e89632b6195c9f50b94f4f9b7271775315afc9940396ed90b6acc534e5'},
        'statement_sha256': '5105e7eedc26bce186b410dbde672fc8a49e6a6195ab0afffe9e6396d82bbd08'},
 2830: {'batch_count': 14,
        'batches_sha256': 'be14745003b98c6051f9a68993c439695467ab8ac8feaeb4abcb9076db453d4a',
        'case_count': 336,
        'cases_sha256': '800710b9b26a8a0137208909784baeec2c3067c417fe0f6c424e4e05079d6b1c',
        'categories_sha256': '672599d2b647a64dcc2e42d46b3bf17ca75110d0504b95474bcc0c36f490a679',
        'git_blob_oid': {'javascript': 'eeb37483dc1da1f6443d51e755b909bf3708cad8',
                         'python': '3bf9c2747d62f109c912aa93486dc7e527d19e68'},
        'oracle_group': 'q06s03',
        'parameters': ['n', 'offers'],
        'source_bytes': {'javascript': 401, 'python': 394},
        'source_sha256': {'javascript': '4f6a95f72b9238d95bbe92b80cbaff556aafd345382ff805e3bfc1b3711b47c8',
                          'python': '5a7ad77e0560edd27c66b1c26ab65157c3a5e304fdaa6ab3fb9cf498df65aa16'},
        'statement_sha256': 'f0aabaeb45945084201f8f76b77d7ea757810ce1d919c22f6321de6e6eae9b92'},
 2844: {'batch_count': 35,
        'batches_sha256': '12d2aecb7b9faf6a6c212551c8ffbdef778aa82755918107a582289a94fa2836',
        'case_count': 1116,
        'cases_sha256': 'd3632cc56ce0d172c2450eb1cb8b8b8927427ea0edbb4fb0c363b1c211b66afc',
        'categories_sha256': '371d7fbfc46d0cff03090a76a6d6d3c0b798eac27b454781c18a92ff26850917',
        'git_blob_oid': {'javascript': '91cf7b8f2559036aaf4f9ff734e961e4bdd75814',
                         'python': '204b01a0c197aabdc36b2a0c47ca2986b3987fad'},
        'oracle_group': 'q06s03',
        'parameters': ['num'],
        'source_bytes': {'javascript': 606, 'python': 551},
        'source_sha256': {'javascript': '51050de4e9ccb154fc7c7a36ea385d041bc88898ff0a4f7dab55d6d4f788c889',
                          'python': '601543781a9dc220c6d76e4ce40b49c5eea451b05189af009f3b362f13d89eb9'},
        'statement_sha256': 'bbf63dc9011c0d778c13d0b26ba7c014866ec1318c3b75c37556db712e3183f7'},
 2857: {'batch_count': 52,
        'batches_sha256': '89a96eb388c13e12201ce7a06a4d60f212251f646bd3d2264e4c704e5c321e4d',
        'case_count': 1548,
        'cases_sha256': '1ceaa0c933fab904f80e6fe1215bf4b4b1ed69471101a159c68a3e921243ac6b',
        'categories_sha256': 'e5c6b4ea79cfb1688bc6dce8c69b9bd1dc5f663d1cf6af7daf8e1e49bafe27fe',
        'git_blob_oid': {'javascript': '94aada43418c1b157036b1e76d0fe6a3294bb7f9',
                         'python': '61193b91cc61cbbc0f78fd3a00861aeb26af160a'},
        'oracle_group': 'q06s03',
        'parameters': ['coordinates', 'k'],
        'source_bytes': {'javascript': 383, 'python': 314},
        'source_sha256': {'javascript': 'f9de33a331074c25ad038e9d9eaf83435eb23979057a95322157c2d02ed866a3',
                          'python': 'e39e3a89fbe99c55ef8fae1fe3353c23b44f1fdf8df11c69b354d016df702775'},
        'statement_sha256': '32c9b4f6525112eff1622c02ef3d1825e7ff4864c5a7baca5f99b9c6a72784f3'},
 2865: {'batch_count': 13,
        'batches_sha256': 'a6e743b7ef0d5338ece3c0ec56cdabe106826cc4293a68a0a912529184288121',
        'case_count': 412,
        'cases_sha256': 'f5427a8a0422f5b5b1f0f5e76932e2ab3b8fcf8cecae22a417ee5a6e97e703d9',
        'categories_sha256': '8f80d4a23ac4db887229e10366fbd0123af7a77963be0b7ad7a9b68123f80924',
        'git_blob_oid': {'javascript': '7ac46cae34152e0f06383c58a60fc174d0145136',
                         'python': '5a36e73968c5506fdb579550da3cffbc2d512e84'},
        'oracle_group': 'q07s01',
        'original_batch_manifest_sha256': '67f00432d64a026674eff728d5ae7b9abbb496f3d52f40f99b28ab513b9485b3',
        'parameters': ['heights'],
        'source_bytes': {'javascript': 626, 'python': 621},
        'source_sha256': {'javascript': '7406457e05644458fbe1fd2fbbb0d2682fef2bbcded4c4a72e0bdcdc4ae9901e',
                          'python': '106c311f422fd360b780d1aa9826904c4bd262cd2874c063f976a6e59859b618'},
        'statement_sha256': '99f3e6681147cf83c561dc265395f753dacd9dc37b346c68e10514d9e300f817'},
 2899: {'batch_count': 36,
        'batches_sha256': '281c5ea1ec3e058d138ec012e73a957175adba7adc025e84dd4139cb7a6ba566',
        'case_count': 1140,
        'cases_sha256': '14d573c669257dbb314da348d0cdb4092adcac7a31f88307ce6b7b75d09214a3',
        'categories_sha256': 'f1c273a614ef7b1caac815e5a8fecf76bfe271d8903fdbddd6cdda64c57bd402',
        'git_blob_oid': {'javascript': '575176bbfea3eed79943df44ee00852f4461e8bf',
                         'python': 'c8513d1c2ebeab794399c307a3630aad2ace7464'},
        'oracle_group': 'q07s01',
        'original_batch_manifest_sha256': 'cd12ad2e9df003e883115b7eea3bc51a5cbf533d333118d4f052c58dd868f380',
        'parameters': ['nums'],
        'source_bytes': {'javascript': 495, 'python': 477},
        'source_sha256': {'javascript': '4f68830f5f2ac45ca1d31a57d08b2e7ad8736cbe8c1810fc21aaa8fb2b94e662',
                          'python': '82b72cdaff9d7a0012305fe46949b04f87cca72097f412581731f7190f8ded7f'},
        'statement_sha256': '9064616e9a73399408383b3684a0c203d6be4d34bb1a2f7a8ab90d9b337ca86c'},
 2909: {'batch_count': 40,
        'batches_sha256': 'caeece93b736a65f5979383c76ed96d4623e734653d21e1a3eb195c4a3c0745a',
        'case_count': 1128,
        'cases_sha256': '1f07f0f4165ebd91ac895395f164a1da526fd032e60fb834acb2ce9af63f58d3',
        'categories_sha256': '1c08833e5a0db2cf1b60602e455dd84615c14d137f9d03ffea607037d2c41b9b',
        'git_blob_oid': {'javascript': '117b5de007f1ad9c58aab047ce9b77cfe5f3fc4a',
                         'python': '58bf62436516e43fc13455ffec07c3c873dd0318'},
        'oracle_group': 'q07s01',
        'original_batch_manifest_sha256': '70638beea5d1b589a5a4c471252c14b128081244556254b0a82e1f561429d1ac',
        'parameters': ['nums'],
        'source_bytes': {'javascript': 642, 'python': 621},
        'source_sha256': {'javascript': '715e4f1748c319eb0b30336e20d1990a6975603545e1b72b48027c012a074275',
                          'python': '07097fa83066644fcbf9fc8cb6720dc0de11395a2deb30520ba0dde832b3d450'},
        'statement_sha256': '9b079f70b998a2ffa34cdc749e91f6b99bb5906213a4b465cbab6e24cf94e14c'},
 2924: {'batch_count': 20,
        'batches_sha256': 'e13a1034538c3c74cb85e0c9835fbe3c10f01449ab7c9737cd9ffe72a90dfe4d',
        'case_count': 621,
        'cases_sha256': '77d2242be9ee3b976653148541d5f6898e47b76ae37bdde95a6446beb845b5c4',
        'categories_sha256': '9899b45d2f5798dfda93b27e936cbf7f120373f288c64cf73f5f7130043f2091',
        'git_blob_oid': {'javascript': '57f9fb4acddd184e9271b84754b0b8360b52d587',
                         'python': '8f2c3a757193839cca8644f8fe02099cd38f4355'},
        'oracle_group': 'q07s01',
        'original_batch_manifest_sha256': '843db1712d2b6f356781f35fe686e4b1d893662f4ad1b135026f28f519d2b7d9',
        'parameters': ['n', 'edges'],
        'source_bytes': {'javascript': 525, 'python': 463},
        'source_sha256': {'javascript': 'fe7db226846b7a9909422a65dc3a0c7ce4e8365a117f0537a36e9c57b0b0d40a',
                          'python': 'ccff479e55182ca3ecd4212b9572df10f55f541895bb6172519755c2a9887293'},
        'statement_sha256': '64b3bae24bb6f397f1d4fddc67288a7af9b1137886f3bcfe8320bab502cfb975'},
 2957: {'batch_count': 45,
        'batches_sha256': 'd693a719e01914561d6f193c2654564a49bbe7a1a233fecf0243cdf123f6d34f',
        'case_count': 1413,
        'cases_sha256': 'e96b7222b87ad01748a328451b42dda18b0390d02b56c11220b8830e3a34272e',
        'categories_sha256': '19376497e2eb7b040af62b7f4f58117736daaafd3de3400cc9265af2a49f6c2f',
        'git_blob_oid': {'javascript': 'f7660550ff93aede45c8e4135987f85271fb467f',
                         'python': 'fdaaddd72f89c15c4676ccd9803058eef4654296'},
        'oracle_group': 'q07s01',
        'original_batch_manifest_sha256': '3de7585daa8e1593cd029f4ef6cc9fae7c5ad9756132b7d55673514bee9a1479',
        'parameters': ['word'],
        'source_bytes': {'javascript': 484, 'python': 444},
        'source_sha256': {'javascript': 'eba476eeb213faba45ee61e78a91a2b6aa9c2ee53ca2e40193605956afc5f70f',
                          'python': 'd1ff3b0b38672aa7c4435a400f213febdf54bba976e522c5d89b22bdc325e02e'},
        'statement_sha256': '49e50b93b095f0355ee41e2ffc529cc5335c1e35ae0562eba1f10b984476cc35'},
 2981: {'batch_count': 18,
        'batches_sha256': 'd4f39f9c0cf68432c82d5a773d8526032b7dd79830109bb440bbbe44a25d7bba',
        'case_count': 570,
        'cases_sha256': '96fa1a499c616b5059fa9a4752d36684229fb59effb22304649ae4beb4d00fcb',
        'categories_sha256': 'd6c449eb0319adc81ef0c507e383e0de37554ec0e545344e0336a49512d51941',
        'git_blob_oid': {'javascript': '932fcebd3ea76141d4823235254cfa898826611c',
                         'python': '2c0a741a46732228dc56cb11ae32aa4b8715d268'},
        'oracle_group': 'q08s01',
        'parameters': ['s'],
        'source_bytes': {'javascript': 425, 'python': 400},
        'source_sha256': {'javascript': '9f8c14a0e2af6856cfcdfb031e597454eaf15fdd1d28d317dd327eadc4302c8f',
                          'python': '901dc83b7d98a9657d226970c3c00fcb53956a47601938e790fb8d992beb2456'},
        'statement_sha256': '0b6727432ac65b2b70edf666929d56afc996ad569acbe5958f87b719e739b218'},
 2998: {'batch_count': 41,
        'batches_sha256': 'c436ce349efe3d1a19285b99f98d9bf5c0bb7577ed62fbf3ee10f6b91f7c8c25',
        'case_count': 1299,
        'cases_sha256': 'f837a783385f94a12bfe2bea46aa3fda4435e63a111a9d47867d34d6c4b4037f',
        'categories_sha256': '3a6d19da85e19ff54f73d1af46aad75e066e1c33e705203804f1431c4e44e9b3',
        'git_blob_oid': {'javascript': 'e5672911897ee768b7d33ca713e177c65fea7544',
                         'python': 'b121e688bda8bee9feb0616f264a181e350fb656'},
        'oracle_group': 'q08s01',
        'parameters': ['x', 'y'],
        'source_bytes': {'javascript': 739, 'python': 769},
        'source_sha256': {'javascript': 'a0c41db5a0fd261b18641800b66c9033f9c389e37f81cff222782631d7db0bf1',
                          'python': '8e40fa9050bd652aeb3e21868d757505cb66b023fb8e0a014a26142d11e19335'},
        'statement_sha256': '6d7dd6e78586e831c03932a7b39421c1e501f5896f40e29b80b05af98e24c90e'},
 3002: {'batch_count': 11,
        'batches_sha256': 'a69e89168f62f9f5ba9e9c0b7c5de7335df66ce7ce45547616e370c619ac642f',
        'case_count': 338,
        'cases_sha256': '42aa8315a2ab13cf59e964d51a573fae8ff7716e3b2715899e3e7afbf6557248',
        'categories_sha256': '477b68791814e45dad17b1e2f830c1478f7c11ebd643153752b294bc56f272d9',
        'git_blob_oid': {'javascript': 'd8b4b10691bac9836128ac9866268d0ca60f52f8',
                         'python': '4d2c0c5871b259c1ac65ca947291e2040c612f4f'},
        'oracle_group': 'q08s01',
        'parameters': ['nums1', 'nums2'],
        'source_bytes': {'javascript': 304, 'python': 228},
        'source_sha256': {'javascript': '2441fa1c7a8fb3b8015e32599f8ae7fdf1d6313b42f8d7f2c95454e1b22dc8c9',
                          'python': 'a6df5e0a09e7e51ac97a7b0d5f026b66867d413c727a629f28a9af63f84ce6ae'},
        'statement_sha256': '6ca97c47690816e6b03f39d5823192079c4ab1264577ecff2b8cab6742ed59f6'},
 3006: {'batch_count': 293,
        'batches_sha256': 'a318682a7d1d88c6a389c4eced2c940a9cb82e1e7cf44e8bcbe0e1e70f516343',
        'case_count': 9373,
        'cases_sha256': 'a7dcf5edc4bbf49409d94986d05ac350e7945abc67e839d2ec88b598e49cf928',
        'categories_sha256': '72c3dffc3331d83ea1bc69ec542fed742a3d3c7cf516c8e96a41b4e364b19e6f',
        'git_blob_oid': {'javascript': '17c7cf84f4dec8c9831aa5a53fdbf96f1f6f88c7',
                         'python': '8fdb1353d6a9824faca8608aed6d2ccc5673cf17'},
        'oracle_group': 'q08s01',
        'parameters': ['s', 'a', 'b', 'k'],
        'source_bytes': {'javascript': 416, 'python': 422},
        'source_sha256': {'javascript': '64eef09e17147d4997554e2bd5ead946f65f4d92dcb5a0060332ffa4691fb861',
                          'python': '7dd79e8bd9a2dc2cf721b676f5d755527431686499895e68c3552c524e3ede26'},
        'statement_sha256': '285f86ee15034e182abafd2fa7e3d2bc2f85b1e849e24f93fa8e19b60bfb8e3c'},
 3012: {'batch_count': 17,
        'batches_sha256': 'd88a96741b50d3d28cce4eabc1640f9e2a0340eb649a53a7be3943cc06dcca63',
        'case_count': 515,
        'cases_sha256': '5f4d0c67369afc3fc5fe628d62637ca1e049fc77dcfc12eb5d4d496d42f00258',
        'categories_sha256': '1c5e95c79551a1318a0b51224158c285a89694a24f7f960d64424bd0d223da30',
        'git_blob_oid': {'javascript': '323164b15dc88049118308053fca8d7f15bbdf9e',
                         'python': 'ca96024a043ae37db7221ba5981025ee1585a9af'},
        'oracle_group': 'q08s01',
        'parameters': ['nums'],
        'source_bytes': {'javascript': 505, 'python': 404},
        'source_sha256': {'javascript': '127bbf4cb8cc795ba319d1bf2f2e685d73d98a6c52a0458a04b3adc31c0ecfea',
                          'python': '2058dc0a8117e6cbaef9d304fe503e85b47a6a99ec564fc10ecba695dbae64cb'},
        'statement_sha256': '1a49f0aa521b69495e7a029e9b04c82f70a2713ef36c763fe680a80a4bc609ff'},
 3016: {'batch_count': 13,
        'batches_sha256': '1937267aa91091cb76bf1bfb27173431d0bf2398df6f38306c0c81da9e299c27',
        'case_count': 404,
        'cases_sha256': '2a41e88ae1219f9a476a3496488f2c1d431b3c3c272dca5b4385f705b30e232a',
        'categories_sha256': 'bbe841a28b4eca8f5b2d6165fe61a088c0a0a6e883350e4cb4c126a4429a4244',
        'git_blob_oid': {'javascript': '53df9e3fd74eca682fea915c09e718934e5325b4',
                         'python': '78e84dc37f5525dfaf8c24011d75eafe1bf99fc8'},
        'oracle_group': 'q08s01',
        'parameters': ['word'],
        'source_bytes': {'javascript': 312, 'python': 246},
        'source_sha256': {'javascript': '22fe0c81ff32f3d7fddab036a902b9759241a25e2b4efdd44e8ff68210289590',
                          'python': 'c6d90ddece3a9299aef17cd942268e688209e72830167fad5ac611c1a9aafb4a'},
        'statement_sha256': '44d6f6d9d8353c80f37fe2728d9134184463e55b729478aea5a25389f60df58c'},
 3020: {'batch_count': 18,
        'batches_sha256': 'b18aa3c75f4f2adb4ae1b075c3177c427df6440ce7a902a9e97b2bed40589654',
        'case_count': 555,
        'cases_sha256': 'ef9d555d0644cab6d7af573ccb46a0a1a78e0a8ae0b277bcef6df310fa9e26bf',
        'categories_sha256': '7bb168b5db13d383ec1ec542df7837cbe647a98a230a27199b8b302b18353b5d',
        'git_blob_oid': {'javascript': '4f666f8bddf18a90054701f23c479490dd77aef4',
                         'python': '579183efefe99d86a9213cf3eac5a3cdd0a87fa3'},
        'oracle_group': 'q08s02',
        'parameters': ['nums'],
        'source_bytes': {'javascript': 431, 'python': 431},
        'source_sha256': {'javascript': '5c82cd1f8cc98d344c7137b66e0c241726167a6d069cbb2a3f6b7f22fa5c19d3',
                          'python': 'f0c09940e6aae4e16f7b52dfd2495aba188588de84c51c0bb9b8539e087e9601'},
        'statement_sha256': '878f1e0ab7ea715f14416c9329448c4b2f9c9847cf2abb7e81538057ea2f67e6'},
 3039: {'batch_count': 106,
        'batches_sha256': '9a62d62b16c266267c9eac29a95ad9a4c0b8f716bca3b3bd02759b40e4aaab11',
        'case_count': 3344,
        'cases_sha256': '1bda52a70c0dba6af3d3ac8539aea74dcc28e4611193f5215ec5ac2cb24f10f8',
        'categories_sha256': '39d099e144a46bb123e1bbdc5f0a113857c4895d50f0be11b436e81d3ada9063',
        'git_blob_oid': {'javascript': 'f165f089d2c51641789fc7cf523c2d6caf77b006',
                         'python': '5bf5be1a691eaf8b56aef868c00baf9ae0fff71f'},
        'oracle_group': 'q08s02',
        'parameters': ['s'],
        'source_bytes': {'javascript': 417, 'python': 321},
        'source_sha256': {'javascript': '575e563cf3b2dff6c1447b18bd41f09d8b1a6629a13e615b2a9e2d0ed180f849',
                          'python': '5fe22e209db5b4eff45ab2212dd75022a20e6caa7ebbcbbe8981f94e019876b7'},
        'statement_sha256': '00feabffb53072b4b3e04dea998beff8066982921c78ac1c1e9c774a331f6673'},
 3048: {'batch_count': 53,
        'batches_sha256': '086a737f20e6d8f9b9db7611e3a226904456e54b7bae95b2edf8f577114200bd',
        'case_count': 1680,
        'cases_sha256': '212b6034ca165d37fdb88e480bbd67f44a854237ec6ba38fe8195bcebda327a7',
        'categories_sha256': 'e41af3ac9b34706334ac5e798cf76f22e6531fc6dd0d02bfcadef0ba465aceb0',
        'git_blob_oid': {'javascript': '4edc867645ac56c7450411599c4fb79958ec52fe',
                         'python': '0019398f74416ae1fb186fbc14da1ca94c13bbaf'},
        'oracle_group': 'q08s02',
        'parameters': ['nums', 'changeIndices'],
        'source_bytes': {'javascript': 955, 'python': 704},
        'source_sha256': {'javascript': '93b75f35492f34b85ec9ef7fe856c94a9226da66298f60d98cfed2f722350a49',
                          'python': 'f6d3b291424a42f4a96600a37d3786f66034e8cb4f6f08892c3290eebd727ed5'},
        'statement_sha256': '99d828033d82e591af479bce678ac331da62b1564e625c2c44a05c3a52d49045'},
 3070: {'batch_count': 66,
        'batches_sha256': '2613e94087ff752e382f4920c024b419ddb88541f3f32bf72b66a044796436e4',
        'case_count': 2058,
        'cases_sha256': '17c6809b0aa2f37478de1b6e5c6e615fc437127a507742d292ff3be5cac1bf16',
        'categories_sha256': 'f6e8525f53a9dfc2fd7e39f12a390777d7dc14755a374292c0deba3b107f4d53',
        'git_blob_oid': {'javascript': '04c5b1fdef98149e215b46327896906749b66e1b',
                         'python': '02d9eb371b91a36ade2d21477ed15766845784b0'},
        'oracle_group': 'q08s02',
        'parameters': ['grid', 'k'],
        'source_bytes': {'javascript': 587, 'python': 542},
        'source_sha256': {'javascript': '3dd801aa92461a4d7d30423761ebd775b6e13f3b80cb5b72de06cc0223f2cc8e',
                          'python': 'a86d7008950db73d49a7302082d5f0a65ab8efca53a8d4f42302b55026d959cb'},
        'statement_sha256': '043f1fe04bfee108d34013344977b1c4d6425ef5833c2c16ec1467ba24c37305'},
 3080: {'batch_count': 165,
        'batches_sha256': '963462d7bd1183630841d3e0194921df8d059c398a6945e91f3638ce224d7d6c',
        'case_count': 5219,
        'cases_sha256': '427597d728a805fa2a26deb637c09d1959913320bce66a73c1aaa6e1a2a1dcf8',
        'categories_sha256': '6f65ca0816bec6b675636918fc75cde924d3d97937c356f6dbd9153c8597c128',
        'git_blob_oid': {'javascript': 'fc2c2b14fa0bb7f4b0fc5e82cc93116f0d4771d1',
                         'python': 'bc4d42f12e68ade5dd5623c2c2178ac9ce2f6b0f'},
        'oracle_group': 'q08s02',
        'parameters': ['nums', 'queries'],
        'source_bytes': {'javascript': 559, 'python': 488},
        'source_sha256': {'javascript': '5f6b24ba5e804531114d758088caaffcf1a9fec7450e761e9191559c4236c0ab',
                          'python': 'bbd813dcc23a0977b13c2119658bef01651ed09bb111f686a6eec120c0242f40'},
        'statement_sha256': 'f76151ea51d496561f3fc7f31586c831f66d5b7b65bd393c4da5bb03f99acf60'},
 3081: {'batch_count': 12,
        'batches_sha256': 'f027419a423213f2d790f9c7be52ecacb6e1cf45fe77870ebebd21b1b20714b9',
        'case_count': 373,
        'cases_sha256': '695913205d996e363a5d58509c8ff494600dd171700642972c5c9a1f16565a67',
        'categories_sha256': 'b83326d65e105ce49a49b14e4ca08ea8d108d67e556f7f943a6f6dd0e5b8aac2',
        'git_blob_oid': {'javascript': '05169c5828e498c4ba125eb52a324f70e3dfdd14',
                         'python': 'b722fbb8ac531af28e459ab2a1f9dfd1ec7d4610'},
        'oracle_group': 'q08s03',
        'parameters': ['s'],
        'source_bytes': {'javascript': 681, 'python': 627},
        'source_sha256': {'javascript': '8fa56f01a97ba70214c3f3d5b9d1eb979af0f036f1f48865acd5124164cae630',
                          'python': '673c830857414ef21f3840a52a91a620dcdf0cb3abfdcd9a646f92d9d8e91e97'},
        'statement_sha256': '09fa673a79c3745779d3961aa1cd3d3f146fff83c1d9a0a59e0bf8da6e6b1d71'},
 3085: {'batch_count': 48,
        'batches_sha256': '14a80dff9ca079212c3c77bf9a9b0eaaee210099e8fd9d06f51da3f5770ca9be',
        'case_count': 1517,
        'cases_sha256': 'a831da8231f649c1ea83cd6b497a9398561453027e1d01e193a1e8176668b0b3',
        'categories_sha256': '44f709672cc1c711aba6912d773aedff99e9275d6d81b7a5a8ea1654430175bd',
        'git_blob_oid': {'javascript': 'ee8f55a00fb9cdc0bc958858f2a178422bb15243',
                         'python': '126cda9982db1f256a4a237ca74d75c232abcb22'},
        'oracle_group': 'q08s03',
        'parameters': ['word', 'k'],
        'source_bytes': {'javascript': 353, 'python': 288},
        'source_sha256': {'javascript': 'fb4f10136862a183ed6ce3bc29639f00252f743e966a7d2b43a639baaf77fe41',
                          'python': '763c87b6f1a151aefd3fe039487c152a10fbef453f730fd633c87eef57016f93'},
        'statement_sha256': 'b2d484f27057dee9e29ac929ffe9790b3177bb1cec7b1fb990ae6870fe46af76'},
 3096: {'batch_count': 258,
        'batches_sha256': '0cdb99df5bae6a50b8751f6cb89dbc613f975f06178a086d589d28348526c9a0',
        'case_count': 8240,
        'cases_sha256': '2e4d9668ff4ba78dff2274ae38a15fd0ebd77d980ee7f9f07849feaaca8c0fa1',
        'categories_sha256': 'eb976c62af5da46d119288a90be4ee342fd2b0212b687ade7ed1ead228fddc17',
        'git_blob_oid': {'javascript': '8221c408db39615af15f2450ba68e6e403c565e2',
                         'python': 'a8443ba5c1b8fa43216b15a78a9388c8f4142580'},
        'oracle_group': 'q08s03',
        'parameters': ['possible'],
        'source_bytes': {'javascript': 303, 'python': 287},
        'source_sha256': {'javascript': '62804acd638a64e132aac8d647064f3d40eb5400520bf30c179d9aaa0a5a9464',
                          'python': '23bb00a44fe4f224e4fccb185b8b8e6a378c3a82cfc9639887eb73a2aa2d45e6'},
        'statement_sha256': '31fa9390a9cf004310a6c12ccfad93b0f78bb5f626c58c0f50147a9ee437c88f'},
 3101: {'batch_count': 258,
        'batches_sha256': '73617e14281194d4c11e2fc6b453c9ab5cbc84b41c8d0e0952abd84e86fab0e6',
        'case_count': 8243,
        'cases_sha256': 'c46b366a51b958a7c3ac33a6c5f6a2cba5a30ac0ee14788e8a5426b60febfae9',
        'categories_sha256': '4fe3b7a2d4185e83129c422e833d62ed00ee5ba2838b9f034c86154e532ec9ba',
        'git_blob_oid': {'javascript': 'd6de7148ea6ae58b182d8d004de040b3b9e1ce28',
                         'python': 'ac41d8fafc3cb939ad871fc16ef7c3e707bfc694'},
        'oracle_group': 'q08s03',
        'parameters': ['nums'],
        'source_bytes': {'javascript': 441, 'python': 413},
        'source_sha256': {'javascript': 'e44a6aad3a1431253d07880b1640b7cff579fe66acce3486e5fd6a226e4a8840',
                          'python': 'a895ffdcf7a7d0e95349db5484199ab23f1925506c99b084e3d6145fb1818386'},
        'statement_sha256': '8345c623a1fc1511d0a583892bedc5feba8b4c6b74fb8a51b210b8d8a7df2737'},
 3106: {'batch_count': 172,
        'batches_sha256': '8c391659ba55c1cd8cc76378a186fbfffa77db2436c15cf75d7e7f75355c9575',
        'case_count': 5481,
        'cases_sha256': 'b2479b0312d1fd0e184cb40a41622b660a25ed4719415c9847c07d9fa2dcd1d0',
        'categories_sha256': '378f082865a930cb1e7644b6bf7f54086ff21372f6a9770914250dc789b34837',
        'git_blob_oid': {'javascript': '11db07525d6eb57611bee5f25cb6e389f838cbf8',
                         'python': '979a0de368cda36884e07b85c5a6d65235f1604a'},
        'oracle_group': 'q08s03',
        'parameters': ['s', 'k'],
        'source_bytes': {'javascript': 359, 'python': 323},
        'source_sha256': {'javascript': '23e700991368fde00442b0c05ccd3b093ecc237374192584611e82d2de7dc738',
                          'python': '8445d2b8f6e320d956f049e18bbd541cdcfa77073b258f6b195464f1dcd27696'},
        'statement_sha256': '4d36bfa542f592a3721c8b7900892c707e868aaf5beb80ed1b929aeccdd8594c'}}

ORACLE_SHA256 = {'request_git_queue05_subset02_oracles.py': '162f3c313e1470f686892734361f508631a75b0fed7119af0304002bcfccb6ca',
 'request_git_queue06_oracles.py': '6fde74e496c72d7d4e167ded33943fa14409e32ae9f6712e4ec9b2c0c12ca75d',
 'request_git_queue06_subset02_oracles.py': 'dc5aeae3d6bd00628e580a106eca788e48670beb970d8abd4469e542a65391e6',
 'request_git_queue06_subset03_oracles.py': 'd46a8cadb43e5bb50a934b07cad18b1574a11b96e75068c31f1d62e7f19e8da7',
 'request_git_queue07_oracles.py': 'd6a849235a929df6de6a38df741c61f57e04d176c96f5b74bbdb7f37736cb13f',
 'request_git_queue08_subset01_oracles.py': '393184e0956e87edddfb8b61e43f881823ce5cbd0cb1f82aee872a3ae76b8328',
 'request_git_queue08_subset02_oracles.py': 'ee754e7e2f3e1c9c605bda82b72224c023def4cd4e589803da3887d4eba68542',
 'request_git_queue08_subset03_oracles.py': 'd557d3ce8bd8f6b979cf77f7e9177019ae339464113e795089a17e070b461c45'}

EVIDENCE_SHA256 = {'historical-support-relocation.json': '4fe4b490ed1d55c2d0c8294e7e78938018c16745b187c171650bfe8f8e4c23c7',
 'q05s02-first-review.json': '8d5174b2a319a74193e1a467ccac8504304af027ecc45885f648a9c727882290',
 'q05s02-manifest.json': 'fe5654f23c38b8994cf3d68ada57dbb99092d2be323bdb7371536a650011839b',
 'q05s02-oracle-review.json': 'fc7bfaebae0730a22183f3a489e87c29f2f2778a98a31341178ea5c9c0b768eb',
 'q05s02-pre-source-review.json': '8382189c8a750ea3b28b7bf0d075861b755387a46e939d058d9b650514cef561',
 'q05s02-pre-source.json': '8248ab04cb1a51fb4b8cdf7a4af584f265a8f39d573d20326df300d84c179655',
 'q05s02-second-review.json': 'c3dbdcaa518305c9eb24c5912ea319b61fb6606d3bacda339ac0f4166e4a9d92',
 'q06s01-first-review.json': '69867af0e8e698e2a4c83a283d1e02b3cb9c854b149315c721cffd7b79cca353',
 'q06s01-manifest.json': '2d5ef43b438c3c8a4b94d790388e765713881c443684e89f5e9eac1c2fb7eaa5',
 'q06s01-oracle-review.json': '74176515fcbe87d55a2b77a84fec8f4716354f613fa83d90f844be6a2090630c',
 'q06s01-pre-source-review.json': 'cb47edc64ddb386ecfbb606b523040f0d3fd48279bbca3376e3653f424603575',
 'q06s01-pre-source.json': '456751b8e2fbcd38015a98983d6f1115131e9866d960da42d5ef6ffb6c01d8ba',
 'q06s01-second-review.json': '88bc747ef2bb027324d255084c648833f93c67ba02a243e0c87555a1c6444139',
 'q06s02-first-review.json': '7d39416fcdf8cb0f73ae919a7cf472468db42c11b4c27f6db77e34a0f0f8c789',
 'q06s02-manifest.json': '0de7a1133932a1f038ba85d539a092dffebe9f4cad31863f177f14d5cd78dad8',
 'q06s02-oracle-review.json': 'e4f9eb7b10cd2b3c16d2abcc0da09b904e20ac1b9e288bc0b75c8d72504f7fdd',
 'q06s02-pre-source-review.json': 'cb47edc64ddb386ecfbb606b523040f0d3fd48279bbca3376e3653f424603575',
 'q06s02-pre-source.json': '6917bcd9e2710a13311b38992f0ab2763d03e12cfc7554177b39681cc21dc1f5',
 'q06s02-second-review.json': '4d5674e2714a211866b5997ca257bc11c2486e2cd7a2149349c6008fa5265553',
 'q06s03-first-review.json': 'a95284c0913eacf4ac5c856a91caa82b858a9d556e72f45933cb9792b7e6cc81',
 'q06s03-manifest.json': '0590a3dda0e63a5d7f8560c50b71bf3ae29e9c3f67b39e0519f03c2c250ffae4',
 'q06s03-oracle-review.json': '5a0b59a6a9d4ee18e7534d1d2645b8c788fe9bcbe8a95f2572bf37ac8d197c79',
 'q06s03-pre-source-review.json': 'cb47edc64ddb386ecfbb606b523040f0d3fd48279bbca3376e3653f424603575',
 'q06s03-pre-source.json': '84b553173762ec20ee503f099d9275ab7460b6bdc85c9f0f6aacf655ce401220',
 'q06s03-second-review.json': 'd8058dd40fb8b61abaca2c3fa60db6df3899473a1a9ab5bbf720ad98e0d03928',
 'q07s01-first-review.json': '3aebe523aa3c745cd44af33f5180f0c6937252b76282a53cab031f594b90cb33',
 'q07s01-manifest.json': '397d9edc8269f506639a887885b2132dd14204ac0c7fe2974b0a72fd217bf358',
 'q07s01-oracle-review.json': 'eb1476387e7aff5d9f2e1658aa3513f15c6cfc283059bda8d8abb3b3d9816e05',
 'q07s01-pre-source-review.json': '5d2eea5dab835511c8cd8c148a90679fd433e877264a3ce6a1a8f8dece245a0a',
 'q07s01-pre-source.json': 'f79995d9be15f99ec6d4b4b778657689d6ae74a33a77cc7f5e179a478f9b2e34',
 'q07s01-second-review.json': 'e7f639bab89e9d24adda5e9aaa7494967e95813d6f31e276e401bc9e7a90b29b',
 'q08s01-first-review.json': '67e578796115234f805bedc5cb1dbe904e7bde71ebcb05f2437cf4a5d747a650',
 'q08s01-manifest.json': '4eaf249f4b8538a5ffe7efaf66ad427b1f4c5b0ecfa37533b9c48210750fb4ba',
 'q08s01-oracle-review.json': '863ce9b1720a45be26947304dc2b37d5689622b43beb8a5018d67196fb2d156e',
 'q08s01-pre-source-review.json': 'b0c4fbbff2e15796d44ee6550facdbe3760e34072f151a3606f6fcb488901f48',
 'q08s01-pre-source.json': '522c49e48b5404bdfd7655a79bfbf89da445d4f09ff110370aff4cb5675b3af5',
 'q08s01-second-review.json': 'b6fec1b858555f3009efe95f7acb5f2f7a2356d32845864353f36b9ece2574f5',
 'q08s02-first-review.json': 'e7356ee43f239ffa022d48b29a4f2a94f04bc328d05c17a4dbfa5b60bd3f60ed',
 'q08s02-manifest.json': '37893ac2a5ceb7e5258cfbf23d91e2c6220cd1cfe2152c5baf8798631553aa01',
 'q08s02-oracle-review.json': '79321acf07a2e1bd2be3ceda600c2870d942e9897e8d5a635537013599878960',
 'q08s02-pre-source-review.json': 'abc610005d1d697061c37b14573b8cd19e85b51faa3553dfbd7cff0fa7e7da99',
 'q08s02-pre-source.json': '3a352a30cc11b67a3ee2a83553ab869c75e69f3ed1d18dbd10130236cc6e66d2',
 'q08s02-second-review.json': '321535059d984fb7be5aad9e87b8333c5b20288da696b47a7d38eddf3a69a66e',
 'q08s03-first-review.json': '7a1c6ec48a3baac285132a15975ac6c4a64733f5a511f0d16a15b69caf6600ff',
 'q08s03-manifest.json': '596f87cc931ecc5fee1c37a2cacd76b143d82ec57648442a0d526136befef51d',
 'q08s03-oracle-review.json': 'cbff2e1eacd76723e0f58f2deba53bb3e9680ec4854540ec6cc1968f0c99ce84',
 'q08s03-pre-source-review.json': 'cee1834514ed6bb33dfb784cc98dea90425de4db18f4906e1b4f0cf54a348ce9',
 'q08s03-pre-source.json': 'b9e93e1bedcf851eeef73e025ef7c9e03cc791a3999e110ff5158ba146357d6f',
 'q08s03-second-review.json': '1c55810fbbbbd4014b46825042c35ac1a53cd4d1de9ff288147c624056f4b196',
 'queue05-chronology-hold.json': 'ce21e96e912647f5a7ec4ca9d4c76f57071c452d626030de6210e9211e04f39f'}

REVIEW_SCHEMAS = {'q05s02': {'first': ('gamma.queue05-subset02-first-static-source-review.v1', 'rows', False),
            'second': ('gamma.queue06-independent-second-source-review.v1', 'records', False)},
 'q06s01': {'first': ('gamma.queue06-first-static-source-review.v1', 'records', False),
            'second': ('gamma.independent-second-source-review.v1', 'rows', False)},
 'q06s02': {'first': ('gamma.queue06-first-static-source-review.v1', 'records', False),
            'second': ('gamma.independent-second-source-review.v1', 'rows', False)},
 'q06s03': {'first': ('gamma.queue06-first-static-source-review.v1', 'records', False),
            'second': ('gamma.independent-second-source-review.v1', 'rows', False)},
 'q07s01': {'first': ('gamma.ordinary-source-static-review.v1', 'rows', True),
            'second': ('gamma.ordinary-source-independent-static-review.v1', 'rows', True)},
 'q08s01': {'first': ('gamma.ordinary-source-static-review.v1', 'rows', True),
            'second': ('gamma.independent-ordinary-source-static-review.v1', 'rows', True)},
 'q08s02': {'first': ('gamma.ordinary-source-static-review.v1', 'rows', True),
            'second': ('gamma.independent-ordinary-source-static-review.v1', 'rows', True)},
 'q08s03': {'first': ('gamma.ordinary-source-static-review.v1', 'rows', True),
            'second': ('gamma.independent-ordinary-source-static-review.v1', 'rows', True)}}

HELD_OUTSIDE_POPULATION = {'queue05_native': [2502, 2526, 2642, 2671],
 'queue05_subset01_exception': [2508, 2567, 2640, 2672],
 'queue07_future': [2896, 2939, 2949, 2962, 2920, 2925, 2967, 2972]}

OLD_LOADER_SHA256 = '55ff4173f9dab55de26dcfe502f60b33ecac96fd3ec9689b150cba58daa4b547'

FUNCTION_LOADER_SHA256 = 'b4811fa56db9e34efd62a2543f93f9277ebda90b739b4a2c029bb7e04606635f'

LIMITATIONS = ('All cases are exposed development evidence. Two static source reviews do not establish native execution, '
 'universal correctness, fresh confirmation or catalogue adoption.',
 'Each immutable oracle manifest and pre-source contract retains its complete domain, numeric contract, '
 'finite design, omitted maximum shapes and complexity/resource cautions; no case/category/batch bytes are '
 'changed.',
 'Historical q fdabf741acaac234a4d83f5667371ce77269b362219ebf6dd1db304edae6ac09 and relocation4fe4b490 '
 'remain historical-support evidence, not live-runtime approval. Actual current runtime and code require '
 'their own freeze.',
 '2771, 2830, 3012, 3020, 3070 and 3080 retain declared valid full-domain inputs beyond the unchanged '
 'MAX_PACKET envelope; finite admitted coverage is not full-domain transport qualification. Runtime, '
 'Node64MiB old-space and large-shape memory remain unmeasured.',
 '3020 retains its reviewed guarded out-of-domain squared-key rounding distinction; 3039 retains O(n) '
 'JavaScript temporary storage. No literal source rewrite or stronger numeric/runtime pass is inferred.',
 'Queue05 subset01 IDs2508,2567,2640,2672 remain excluded under the unrepaired acquisition-chronology hold. '
 'Their failure is neither inherited by unaffected subsets nor silently repaired.',
 'Native classes2502,2526,2642,2671 and future queue07 eight remain outside this fixed ordinary population. '
 'No widened source authority, source rewriting, helper injection or alternate comparator is introduced.')

def binding(pid):
    if type(pid) is not int or pid not in IDS:
        raise ValueError('problem outside fixed cohort02 ordinary population')
    return BINDINGS[pid]


def oracle_for(pid):
    group = binding(pid)['oracle_group']
    return {'q05s02': q05s02, 'q06s01': q06s01, 'q06s02': q06s02, 'q06s03': q06s03,
            'q07s01': q07s01, 'q08s01': q08s01, 'q08s02': q08s02, 'q08s03': q08s03}[group]


def validate(pid, args):
    oracle_for(pid).validate(pid, args)


def additional_code():
    paths = {str(Path(__file__).resolve()): q.file_hash(__file__)}
    read_owners = {
        'gated_payload_read.py': '7fb54acfee9642a7e26f0f13eab99ebda1e7da842ea675a923d5f7e45dbf233a',
        'boundary_policy.py': 'd51e5dde8865db4a10ef319efdfb39d9e34730db2893d5d20bed49b7dff8a2de',
        'public_batch_adapter.py': 'd8c129bc6d405e4ec5d2bd2a403fac2381b593f9b4c90b88a4ef9c6ca2f7fc92',
    }
    for name, pin in {**ORACLE_SHA256, **read_owners}.items():
        path = Path(__file__).with_name(name)
        observed = q.file_hash(path)
        approved = {pin}
        if name == 'public_batch_adapter.py':
            # Exact reviewed replay-only successor; bounded_regular_read and
            # every other owner AST node remain unchanged. Frozen copies retain
            # their old reader identity; new freezes bind the actual new bytes.
            approved.add('8f22f126045f5b6d06e95d16b81d36f6944d857984cb93ff0a7669f19a9cdf2e')
        if observed not in approved:
            raise ValueError('immutable cohort02 oracle or reader changed')
        paths[str(path.resolve())] = observed
    return paths


def original_base(config):
    if (config['catalogue']['sha256'] != '9ab963740caad76bb15d602fb2ab93e2d010f2765605a9b9e63bbaa620dbb329' or
            config['verified_receipts']['sha256'] != '63a3c432f5ec3057dda03a560080f089d70ad4fffa9966a215343d61bd2148fc'):
        raise ValueError('original943 qualification base required; adoption authority stays separate')


def pinned(path, pin):
    raw = q.read(path)
    if q.sha(raw) != pin:
        raise ValueError('fixed evidence changed: ' + Path(path).name)
    return raw


def source_review_rows(group, review, value):
    schema, key, nested = REVIEW_SCHEMAS[group][review]
    if value.get('schema') != schema:
        raise ValueError('unexpected fixed source-review schema')
    rows = value[key]
    observed = []
    for row in rows:
        source = row['source'] if nested else row
        observed.append((row['problem_id'], row['language'], source['sha256' if nested else 'source_sha256'],
                         source['git_blob_oid'], source['bytes']))
    return observed


def evidence(root):
    retained = {name: pinned(root / name, pin) for name, pin in EVIDENCE_SHA256.items()}
    for group, ids in SOURCE_GROUPS.items():
        wanted = {(pid, lang, BINDINGS[pid]['source_sha256'][lang], BINDINGS[pid]['git_blob_oid'][lang],
                   BINDINGS[pid]['source_bytes'][lang]) for pid in ids for lang in LANGUAGES}
        for review in ('first', 'second'):
            observed = source_review_rows(group, review, q.decode(retained[f'{group}-{review}-review.json']))
            if len(observed) != len(wanted) or set(observed) != wanted:
                raise ValueError('both fixed source reviews must bind every exact original')
    return retained


def interface_contract():
    return {'schema': 'gamma.cohort02-ordinary-interface-successor.v1', 'problem_ids': list(IDS),
            'source_sha256': {str(pid): BINDINGS[pid]['source_sha256'] for pid in IDS},
            'ordered_parameters': {str(pid): BINDINGS[pid]['parameters'] for pid in IDS},
            'pre_source_contract_sha256': {g: EVIDENCE_SHA256[g + '-pre-source.json'] for g in SOURCE_GROUPS},
            'second_source_review_sha256': {g: EVIDENCE_SHA256[g + '-second-review.json'] for g in SOURCE_GROUPS},
            'declaration_timing': 'Explicit post-source ordinary-call binding; original pre-source unknowns and development exposure remain unchanged.',
            'javascript': 'commonjs-function-solve-v1', 'python': 'global-solve-v1',
            'javascript_call': 'Native direct CommonJS callable; Reflect.apply(exported, undefined, ordered_args)',
            'comparison_policy': 'exact', 'old_object_loader_sha256': OLD_LOADER_SHA256,
            'function_loader_sha256': FUNCTION_LOADER_SHA256, 'constructor_injection': False,
            'original_candidate_bytes_unchanged': True, 'effects_and_domain_unchanged': True,
            'cases_unchanged': True, 'runtime_bounds_unchanged': True, 'automatic_promotion': False,
            'held_outside_population': HELD_OUTSIDE_POPULATION, 'retained_limitations': list(LIMITATIONS)}


def approved_interface(root, review_sha256):
    raw = pinned(root / 'interface-contract.json', q.sha(q.encoded(interface_contract())))
    review_raw = pinned(root / 'interface-review.json', review_sha256)
    review = q.decode(review_raw)
    flags = ('independent_review', 'approved', 'original_candidate_bytes_unchanged',
             'effects_and_domain_unchanged', 'cases_unchanged', 'runtime_bounds_unchanged',
             'original_pre_source_gaps_preserved', 'historical_support_not_reclassified_as_live_approval',
             'exposure_and_omissions_preserved')
    if (review.get('schema') != 'gamma.cohort02-ordinary-interface-review.v1' or
            any(review.get(key) is not True for key in flags) or
            not isinstance(review.get('reviewer'), str) or not review['reviewer'].strip() or
            review.get('contract_sha256') != q.sha(raw) or
            review.get('old_object_loader_sha256') != OLD_LOADER_SHA256 or
            review.get('function_loader_sha256') != FUNCTION_LOADER_SHA256):
        raise ValueError('independent approval of exact cohort02 interface successor required')
    if (q.file_hash(q.COMMONJS_HARNESS) != OLD_LOADER_SHA256 or
            q.file_hash(q.COMMONJS_HARNESS.with_name('function-harness.cjs')) != FUNCTION_LOADER_SHA256):
        raise ValueError('reviewed loader bytes changed')
    return raw, review_raw


def frozen_row(pid, retained):
    group = binding(pid)['oracle_group']
    manifest = q.decode(retained[group + '-manifest.json'])
    if group == 'q05s02':
        limits, max_file, max_packet = manifest['resource_limits'], manifest['max_file'], manifest['max_packet']
    elif group.startswith('q08'):
        limits, max_file, max_packet = (manifest['resources'][key] for key in ('LIMITS', 'MAX_FILE', 'MAX_PACKET'))
    else:
        limits, max_file, max_packet = manifest['limits'], manifest['max_file'], manifest['max_packet']
    if limits != q.LIMITS or max_file != q.MAX_FILE or max_packet != q.MAX_PACKET:
        raise ValueError('original oracle resource bounds differ')
    rows = manifest['rows' if group.startswith('q08') else 'records']
    selected = [row for row in rows if row['problem_id'] == pid]
    if len(selected) != 1:
        raise ValueError('fixed oracle row missing or duplicated')
    return selected[0]


def batch_manifest(pid, cases):
    spec = binding(pid); oracle = oracle_for(pid); groups = []
    for offset, batch in q.batches(cases):
        packet = q.encoded(q.packet(batch))
        group = {'offset': offset, 'count': len(batch), 'packet_bytes': len(packet)}
        expected_bytes = {lang: oracle.expected_observation_bytes(batch, lang) for lang in LANGUAGES}
        if spec['oracle_group'] == 'q05s02':
            group['projected_output_bytes'] = max(expected_bytes.values())
        else:
            group['expected_observation_bytes'] = expected_bytes
            if not spec['oracle_group'].startswith('q06'):
                group['packet_sha256'] = q.sha(packet)
        groups.append(group)
    return groups


def generated(pid, statement, retained):
    spec = binding(pid)
    if q.sha(statement) != spec['statement_sha256']:
        raise ValueError('exact statement bytes required')
    cases, categories = oracle_for(pid).build_cases(pid, statement)
    if (len(cases) != spec['case_count'] or q.sha(q.encoded(cases)) != spec['cases_sha256'] or
            q.sha(q.encoded(categories)) != spec['categories_sha256']):
        raise ValueError('immutable oracle case/category design changed')
    groups = batch_manifest(pid, cases); row = frozen_row(pid, retained)
    if len(groups) != spec['batch_count'] or q.sha(q.encoded(groups)) != spec['batches_sha256']:
        raise ValueError('original frozen batching or observation projection changed')
    if spec['oracle_group'] == 'q05s02' and groups != row['batch_plan']:
        raise ValueError('original queue05 batch plan differs')
    if spec['oracle_group'].startswith(('q06', 'q07')) and groups != row['batches']:
        raise ValueError('original queue06/07 batches differ')
    if spec['oracle_group'] == 'q07s01' and q.canonical_tests_hash(groups) != spec['original_batch_manifest_sha256']:
        raise ValueError('original queue07 no-newline batch digest differs')
    if spec['oracle_group'].startswith('q08') and q.sha(q.encoded(groups)) != row['batches_sha256']:
        raise ValueError('original queue08 batch pin differs')
    for case in cases:
        validate(pid, case['args'])
    return cases, categories


def record_payload_read(path, value):
    """Append a bounded mutable host sidecar through anchored no-follow handles."""
    raw_path = os.fspath(path)
    if (not isinstance(raw_path, str) or not raw_path.startswith('/') or '\0' in raw_path or
            any(part in ('', '.', '..') for part in raw_path[1:].split('/'))):
        raise ValueError('canonical absolute private acquisition path required')
    raw = q.encoded(value)
    if len(raw) > MAX_ACCESS_LOG_BYTES:
        raise ValueError('private acquisition record exceeds its host bound')
    parts = raw_path[1:].split('/')
    directory = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        fd = os.open(parts[-1], os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW | os.O_NONBLOCK,
                     0o600, dir_fd=directory)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_size + len(raw) > MAX_ACCESS_LOG_BYTES:
                raise ValueError('private acquisition record must be regular and within its host bound')
            with os.fdopen(fd, 'ab', closefd=False) as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        os.close(directory)


def retained_payload_read(path, pid, language, kind, gate, receipt_path, **expected):
    record = {'schema': 'gamma.cohort02-payload-access.v1',
              'at': datetime.now(timezone.utc).isoformat(), 'path': str(path),
              'problem_id': f'leetcode:{pid}', 'language': language, 'payload_kind': kind}
    try:
        raw, receipt = read_payload(path, problem_id=f'leetcode:{pid}', language=language,
                                    payload_kind=kind, artifact_paths=gate['artifact_paths'],
                                    trusted_hashes=gate['trusted_hashes'], **expected)
    except Exception as exc:
        record.update(status='failed', exception_type=type(exc).__name__, exception=str(exc),
                      receipt=getattr(exc, 'receipt', None))
        if record['receipt'] is None:
            record['payload_open_attempts'] = 'unknown; failure may precede or follow an attempted open'
        record_payload_read(receipt_path, record)
        raise
    record.update(status='verified', receipt=receipt)
    record_payload_read(receipt_path, record)
    return raw


def source_bytes(path, pid, language, gate, *, receipt_path):
    spec = binding(pid)
    if language not in LANGUAGES:
        raise ValueError('source outside fixed languages')
    return retained_payload_read(
        path, pid, language, 'source', gate, receipt_path,
        expected_sha256=spec['source_sha256'][language], maximum_bytes=1024 * 1024,
        expected_size=spec['source_bytes'][language], expected_git_blob_oid=spec['git_blob_oid'][language])


def statement_bytes(path, pid, gate, *, receipt_path):
    spec = binding(pid)
    return retained_payload_read(path, pid, 'python', 'statement', gate, receipt_path,
                                 expected_sha256=spec['statement_sha256'], maximum_bytes=q.MAX_FILE)


def make_job(root, pid, language, cases, original_source):
    spec = binding(pid)
    if language not in LANGUAGES:
        raise ValueError('fixed job language required')
    suffix = 'js' if language == 'javascript' else 'py'
    return {'id': pid, 'language': language, 'source': f'sources/{pid}.{suffix}',
            'source_sha256': spec['source_sha256'][language], 'original_source': original_source,
            'tests': f'tests/{pid}.json', 'tests_raw_sha256': spec['cases_sha256'],
            'tests_canonical_sha256': q.canonical_tests_hash(cases), 'case_count': spec['case_count'],
            'statement': {'path': str((root / f'statements/{pid}.md').resolve()), 'sha256': spec['statement_sha256']},
            'domain_validator': DOMAIN, 'comparison_policy': 'exact',
            'source_interface': 'commonjs-function-solve-v1' if language == 'javascript' else 'global-solve-v1'}


def verify_freeze(root, contract, gate):
    jobs = contract.get('jobs', [])
    if (contract.get('selected_problem_ids') != list(IDS) or contract.get('pending') != [] or
            contract.get('automatic_promotion') is not False or contract.get('protected_access') is not False or
            contract.get('additional_code') != additional_code() or contract.get('limits') != q.LIMITS or
            contract.get('max_packet_bytes') != q.MAX_PACKET or contract.get('retained_limitations') != list(LIMITATIONS) or
            contract.get('held_outside_population') != HELD_OUTSIDE_POPULATION or
            contract.get('mutable_access_log') != MUTABLE_ACCESS_LOG or
            [(j.get('id'), j.get('language')) for j in jobs] != [(pid, lang) for pid in IDS for lang in LANGUAGES]):
        raise ValueError('fixed cohort02 job population or bindings differ')
    original_base(q.decode(pinned(contract['service_config'], contract['service_config_sha256'])))
    input_root = contract.get('input_root')
    if not isinstance(input_root, str) or not Path(input_root).is_absolute() or '..' in Path(input_root).parts:
        raise ValueError('explicit original input root required')
    retained = evidence(root / 'evidence')
    approved_interface(root / 'evidence', contract['interface_review_sha256'])
    for pid in IDS:
        statement = statement_bytes(root / f'statements/{pid}.md', pid, gate,
                                    receipt_path=root / MUTABLE_ACCESS_LOG)
        cases, categories = generated(pid, statement, retained)
        if (q.read(root / f'tests/{pid}.json') != q.encoded(cases) or
                q.read(root / f'tests/{pid}.categories.json') != q.encoded(categories) or
                q.read(root / f'tests/{pid}.batches.json') != q.encoded(batch_manifest(pid, cases))):
            raise ValueError('frozen case/category/batch payload differs')
        for job in (j for j in jobs if j['id'] == pid):
            lang = job['language']; suffix = 'js' if lang == 'javascript' else 'py'
            if job != make_job(root, pid, lang, cases, str(Path(input_root) / f'sources/{pid}.{suffix}')):
                raise ValueError('fixed source/domain/interface/comparison job differs')


def prepare(args):
    runtime_identity = q.runtime(getattr(args, 'node_runtime', None))
    KnownSpecService.from_config(args.config, args.config_sha256)
    config = q.decode(pinned(args.config, args.config_sha256)); original_base(config)
    gate_spec = config['source_access']['boundary_gate']; gate = q.decode(pinned(gate_spec['path'], gate_spec['sha256']))
    if not {f'leetcode:{pid}' for pid in IDS} <= _boundary_snapshot(gate).authorized:
        raise PermissionError('fixed cohort02 population is not currently authorized')
    retained = evidence(args.input_root / 'evidence')
    interface, review = approved_interface(args.input_root / 'evidence', args.interface_review_sha256)
    args.output.mkdir(parents=True, exist_ok=False)
    for directory in ('sources', 'tests', 'statements', 'evidence'):
        (args.output / directory).mkdir()
    for name, raw in {**retained, 'interface-contract.json': interface, 'interface-review.json': review}.items():
        (args.output / 'evidence' / name).write_bytes(raw)
    jobs = []
    for pid in IDS:
        spec = binding(pid)
        statement = statement_bytes(args.input_root / f'statements/{pid}.md', pid, gate,
                                    receipt_path=args.output / MUTABLE_ACCESS_LOG)
        cases, categories = generated(pid, statement, retained)
        if (pinned(args.input_root / f'tests/{pid}.json', spec['cases_sha256']) != q.encoded(cases) or
                pinned(args.input_root / f'tests/{pid}.categories.json', spec['categories_sha256']) != q.encoded(categories)):
            raise ValueError('private packet case bytes differ')
        (args.output / f'statements/{pid}.md').write_bytes(statement)
        q.write(args.output / f'tests/{pid}.json', cases); q.write(args.output / f'tests/{pid}.categories.json', categories)
        q.write(args.output / f'tests/{pid}.batches.json', batch_manifest(pid, cases))
        for lang in LANGUAGES:
            suffix = 'js' if lang == 'javascript' else 'py'; source = args.input_root / f'sources/{pid}.{suffix}'
            raw = source_bytes(source, pid, lang, gate, receipt_path=args.output / MUTABLE_ACCESS_LOG)
            (args.output / f'sources/{pid}.{suffix}').write_bytes(raw)
            jobs.append(make_job(args.output, pid, lang, cases, str(source.resolve())))
    contract = {'schema': 'gamma.imported-independent-execution.v1', 'selected_problem_ids': list(IDS),
                'jobs': jobs, 'pending': [], 'automatic_promotion': False, 'protected_access': False,
                'service_config': str(args.config.resolve()), 'service_config_sha256': args.config_sha256,
                'input_root': str(args.input_root.resolve()), 'runtime': runtime_identity,
                'code': q.code_pins(), 'additional_code': additional_code(), 'limits': q.LIMITS,
                'max_packet_bytes': q.MAX_PACKET, 'interface_review_sha256': args.interface_review_sha256,
                'effects': 'Read-only arguments; exact typed ordered returns; no mutable return/input aliases or external IO.',
                'retained_limitations': list(LIMITATIONS), 'held_outside_population': HELD_OUTSIDE_POPULATION,
                'mutable_access_log': MUTABLE_ACCESS_LOG,
                'scope': 'Exposed development finite-case qualification only; no universal/full-domain resource proof, fresh confirmation or catalogue adoption.'}
    q.write(args.output / 'contract.json', contract)
    return {'jobs': len(jobs), 'cases_per_language': sum(BINDINGS[pid]['case_count'] for pid in IDS),
            'contract_sha256': q.file_hash(args.output / 'contract.json')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('config', 'input-root', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--config-sha256', required=True)
    parser.add_argument('--interface-review-sha256', required=True)
    parser.add_argument('--node-runtime', type=Path)
    print(q.encoded(prepare(parser.parse_args())).decode(), end='')
