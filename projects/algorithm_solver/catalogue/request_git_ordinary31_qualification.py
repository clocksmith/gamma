"""Fixed 31-pair qualification preparation through the existing bounded runner.

Not an execution engine or variant registry. Immutable source/oracle reviews and
post-source interface/1943 ordering approval precede every actual execution.
Original943 qualification authority is separate from prospective adoption bases.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from . import imported_qualification as q
from . import request_git_queue01_oracles as queue01
from . import request_git_queue01_subset02_oracles as queue01_subset02
from . import request_git_queue02_subset02_oracles as queue02_subset02
from . import request_git_queue03_oracles as queue03
from . import request_git_queue04_oracles as queue04
from .boundary_policy import authorize_before_open
from .known_spec_service import KnownSpecService, _boundary_snapshot

IDS = (1943,
 1957,
 1959,
 1971,
 1977,
 1997,
 2017,
 2048,
 2049,
 2056,
 2117,
 2156,
 2209,
 2213,
 2245,
 2271,
 2289,
 2301,
 2321,
 2333,
 2348,
 2375,
 2384,
 2396,
 2428,
 2438,
 2443,
 2449,
 2452,
 2467,
 2498)
LANGUAGES = ('javascript', 'python')
DOMAIN = 'request-git-ordinary31-v1'
SOURCE_GROUPS = {1: (1943, 1957, 1959, 1971, 1977, 1997, 2017, 2048, 2049, 2056),
 2: (2117, 2156, 2209, 2213),
 3: (2245, 2271, 2289, 2301, 2321, 2333, 2348),
 4: (2375, 2384, 2396, 2428, 2438, 2443, 2449, 2452, 2467, 2498)}
BINDINGS = {1943: {'batch_count': 11,
        'case_count': 344,
        'cases_sha256': '1f415b3834f0e3e55192dbf71e8c40281e8431363dc33b198842fa95c35385b4',
        'categories_sha256': 'ae6d97b16ce46652ae1fb7ad00a696ed45bba1f904810f4622c9d0ca5c1571b3',
        'git_blob_oid': {'javascript': 'e2191adfe153b04d7263b0e14650c5386bb019d0',
                         'python': '917fd00630821f65f3ff10fb7d60b89656944110'},
        'oracle_group': 'queue01-subset02',
        'parameters': ['segments'],
        'source_group': 1,
        'source_sha256': {'javascript': 'd66a756f027bea724a09f4197e179860d6b0c169df6981724905a5d493c16de9',
                          'python': '4a79804cf0e44dea48d8ee2df48624a21b81a28f683f90934782756a3167a630'},
        'statement_sha256': '50e19746099dee2c61900733bb0084109eca5d90a382ab60e68223a9acaf76e2'},
 1957: {'batch_count': 22,
        'case_count': 688,
        'cases_sha256': 'f5b2103afea47044583a850af95d01a4094c2571b016ec4b5a2830c6032dd485',
        'categories_sha256': '27a8a0b1da11510a2e7004d02c162eb112c354affdf65e4f3a4b12a290e39a8d',
        'git_blob_oid': {'javascript': '1a4e43b21627fc7ec5b6f5d10b98bcafd922c301',
                         'python': '920975b6a5a47c0843fa27e021ee60a3ff2fe6ca'},
        'oracle_group': 'queue01',
        'parameters': ['s'],
        'source_group': 1,
        'source_sha256': {'javascript': '697c8c3aa71bdfd30c4ed6cb598363455c8fe1506c49253f158de770635e28f5',
                          'python': 'f9c45c8febef6a8b68b54123a2afaab138a6a016237f1986a473c35206335aaa'},
        'statement_sha256': '8e84233c909da868fb60aa9f9b2644a4eae6c030fdb01635c8b8a45f6600f3ca'},
 1959: {'batch_count': 55,
        'case_count': 1734,
        'cases_sha256': '3a731874126edb05de82e5677951ba84fceb8d8ea4f7dd6b06a122e8c6d2f98b',
        'categories_sha256': '2285ffaf4c057f0a9621b8de39119747f92b35c737c48b2a43799d9c1dbe9fb6',
        'git_blob_oid': {'javascript': '070ee3e042a1053d950c9b20b883dff188f70bb2',
                         'python': 'a91a4acc2e40351f90001a49216bccf3b77af2e9'},
        'oracle_group': 'queue01-subset02',
        'parameters': ['nums', 'k'],
        'source_group': 1,
        'source_sha256': {'javascript': '264ec53c2521b9108a6979540d319d093bae935fe03b7c1b89bb1b3d5cf68bc3',
                          'python': '01d629671158a61dd3b70292873b15cc09f29b45cac2a549795f138b77c0e13b'},
        'statement_sha256': '690d5b23cc0a83d4060bc0e2aed8deb803f291ecb6d1d1e454bf2ad2acd3c62a'},
 1971: {'batch_count': 37,
        'case_count': 1172,
        'cases_sha256': '09ac49248499ca758d13d35f4701fdf2a965ad7d770b1605ae496b8e4d5a764f',
        'categories_sha256': '8a518a39008de7cb2defb2bdaca9a9d6d04e0b6a2a156c20bb9f4b3d87786c77',
        'git_blob_oid': {'javascript': '9c0f4e243c1cb6976332147308aec5941680604e',
                         'python': 'b771d7959cce2bb01b9523cacba996cfa29ad1c2'},
        'oracle_group': 'queue01',
        'parameters': ['n', 'edges', 'source', 'destination'],
        'source_group': 1,
        'source_sha256': {'javascript': 'c4012d0de9224464394e7c4b3a33c04fbbb466b53b7ea4bc2afd74b8292d5823',
                          'python': 'ada289c243c6b0874ba129b65d22bb0450f8f7769f20f4bac953aeda2fd27daa'},
        'statement_sha256': 'a79f9261c2e2697f2ee27d6268a2135adaf14ae8d36f8feb91e0641ca01d9c38'},
 1977: {'batch_count': 37,
        'case_count': 1180,
        'cases_sha256': 'cb7123778e907521703127b53e4117d3d59504f220f3daadfd5dc5c1e225aef7',
        'categories_sha256': 'ba9ff584422648da53675b7eca88edcc01c9fb48095100b532b6f2f26ed38fdc',
        'git_blob_oid': {'javascript': 'dbbd65ebf4824c86322684fb15fa597a87b5822b',
                         'python': 'e2c260c84432c9a677f9d67dbf3925da2cc46a93'},
        'oracle_group': 'queue01-subset02',
        'parameters': ['num'],
        'source_group': 1,
        'source_sha256': {'javascript': 'e766c20a42d5d6d7346193e0645c8294629c50975cd00eaf703104434612c9b0',
                          'python': 'c962dbd03003ac5118c1796fa3bdbaac614443ec0b11ec86c5e1fe681631eae8'},
        'statement_sha256': '940741373698e34d60afb07aefaa35b926d0f8a2adf8dacd3ef8aa91e54073b9'},
 1997: {'batch_count': 33,
        'case_count': 979,
        'cases_sha256': 'fe794d67e3a4a7c9bdb6db52baef5fc3b5aaa4b7b11f83bc80dc57fe6cd6fb5c',
        'categories_sha256': '5621e8f3f29b4459753bcbfce39e88775629177b36760cb3b008063b78f87dbd',
        'git_blob_oid': {'javascript': 'f0c4458ee3bea7edf00ea7f87e00cf018a877d16',
                         'python': 'a01655182abc2a79c3daefd458181cf83b1f5e99'},
        'oracle_group': 'queue01-subset02',
        'parameters': ['nextVisit'],
        'source_group': 1,
        'source_sha256': {'javascript': 'c3072c88bf53e82d2504fbb03224d9392b2fba8af442bccbf2ea07648944d2fc',
                          'python': '55c9c588cef6dddc035decaa197c843a9c5609420fa603f4777150c9de76864f'},
        'statement_sha256': '37a9643de76f485a5958f8da6a6c5967508b109c868effaa1c88b6e4384aa14e'},
 2017: {'batch_count': 15,
        'case_count': 419,
        'cases_sha256': 'e1371543bd96efca21381a7ddae39d2b6c7d0b52974dfe82fe13a76db7c3bb86',
        'categories_sha256': 'd7d13fdc8b3054b68fb3042bf41f936ce2b424b62ab84c93796ebb87f5e6df71',
        'git_blob_oid': {'javascript': 'a8fd2351e502e729c0e58c5b03df1c697f8b02dd',
                         'python': '359754f6dbb8eb00406f54f5b6786e2d7223bb16'},
        'oracle_group': 'queue01',
        'parameters': ['grid'],
        'source_group': 1,
        'source_sha256': {'javascript': '248ada6d121ee7e7c07f87613fe7b77dcd56ebe8071faba9a6674ad15392c624',
                          'python': '1063daf03de95026faf19e8cafaf337afbd2f2d01a4f50bb070e53f0b945931e'},
        'statement_sha256': '47f4d24e86cf39ba4b45558ad53663a5cd049e8618c33b88cbbb131b70036bdd'},
 2048: {'batch_count': 30,
        'case_count': 932,
        'cases_sha256': '0e4a0397dc260c1007d9a791b2a2aa13b379eb79247c9003f018934bd97e3fce',
        'categories_sha256': '64bc2c0fafe2192022a0ad4c001f945cae83611101d5d3700f16b880072d51a2',
        'git_blob_oid': {'javascript': '7740627a1db09f0b88901618a4f81c2259cbd59f',
                         'python': 'da6b30fe730beccd7aa3d16235142aef85b02f25'},
        'oracle_group': 'queue01',
        'parameters': ['n'],
        'source_group': 1,
        'source_sha256': {'javascript': '3fb292decc3a852d1612e5cd8b32a7f505a6e442e41a69b934e8616e889a126f',
                          'python': '23013bed585eb94b8d769696049b788c7cf9ff4d14074425b6e7c8dbb5a235b1'},
        'statement_sha256': 'aef8e178b2661339fe4c3a0be5a313a75fb3daa1c3db93c69f3549d64aaa5541'},
 2049: {'batch_count': 41,
        'case_count': 1252,
        'cases_sha256': '32ab34f829fc96910d708b7fd8017ee090324ad1c037b94f78e47631b3d76e3a',
        'categories_sha256': 'c184f79056578bcd84c1965ae46c8784277fede37902558a25db0af9f2a4f38c',
        'git_blob_oid': {'javascript': 'c727632c1a5dafebccd2dc764a4972791d16472c',
                         'python': '6186220ba2ed6970213c92e1c392f6b9daaa6480'},
        'oracle_group': 'queue01-subset02',
        'parameters': ['parents'],
        'source_group': 1,
        'source_sha256': {'javascript': '3a39d4fa19310a937dc61476557cb5395c661108886c88b2011f8878dca48a73',
                          'python': '03c6eed9f3388e59973ecfe72cdfc235e70c490cdfddcb78a79df0d64127aae8'},
        'statement_sha256': '61bb299b7c1d02a4e2fbc71a0aaf390dca093f4da331e5eb7f47d8e4127d2cca'},
 2056: {'batch_count': 14,
        'case_count': 443,
        'cases_sha256': '8e079fd1e10749739b493a0a1e3a2b3146016b3a19dd1bc81caa11eddb534855',
        'categories_sha256': '4c0f4d44f3084d14032d04b9a17db898d04aaa82ca049ceaa0a52f81f346e162',
        'git_blob_oid': {'javascript': 'b9cd185266ef916157d9b6184ef2a4ac4ce318a0',
                         'python': '4306959b757096d74ff729472e35733ca559f6b9'},
        'oracle_group': 'queue01-subset02',
        'parameters': ['pieces', 'positions'],
        'source_group': 1,
        'source_sha256': {'javascript': 'a2e02d005b1acb2b79884d22b396c10729b63b539c190564db1a7ebc5b0a9a7f',
                          'python': '38e3de9a476ef584ab526a459d4c69eb76058e9f6cc8ef75305304340d8c862b'},
        'statement_sha256': '7cdbc667949079835e4000cc286878b042b62582adb028bb3b4653e0d9435591'},
 2117: {'batch_count': 58,
        'case_count': 1839,
        'cases_sha256': '97e7502c9595bce9b10d4e1433a638f552f34be087446ff098b4559bcd3d139f',
        'categories_sha256': 'f222b5a8cc2181147470b62345fd22d16343f3c4cc54a545f19556a4437383d9',
        'git_blob_oid': {'javascript': 'da70807e4584159eac2af2d3405a5de344ae2858',
                         'python': 'b80e23d80dda01299ebc4e7560e6aa388b5bae4b'},
        'oracle_group': 'queue02-subset02',
        'parameters': ['left', 'right'],
        'source_group': 2,
        'source_sha256': {'javascript': '05c35441a87c53194a85b5e2d59c346bcaa5eee39b651361b78c603b975ed699',
                          'python': 'a9698745d7d5289b017ff5ca1885b667a06bb3404333b7fb71427215c7c2ef2e'},
        'statement_sha256': '05318d336992bd023dc80cc6e1c1ffc455d4569c66e7961fb74796d134e45af2'},
 2156: {'batch_count': 39,
        'case_count': 1229,
        'cases_sha256': '1bc49415db05dabb07c64813ea80328f4a40b364f07a60c144c7b9ff75b7e517',
        'categories_sha256': 'e5f63e135bebe5ac249e97a73a794fee09e1c8a16ed44fa2da858cbfe186a232',
        'git_blob_oid': {'javascript': '1b48ac6b08da8a270a29cb9c0895b03d978e307e',
                         'python': '102a4415982f42a46f186ee5e39c5515a57561a5'},
        'oracle_group': 'queue02-subset02',
        'parameters': ['s', 'power', 'modulo', 'k', 'hashValue'],
        'source_group': 2,
        'source_sha256': {'javascript': '7ce8020e2e60ad5e456eb3a02961b2bf44b276b18e45291423258ccd1f79efdd',
                          'python': 'df2a90340e932ca58ceeea1faf63af5c849580e87d2ca5fb9dc278404e07e00b'},
        'statement_sha256': '63540b2cfaeff3e39c73111a71ced716feb535b1ab74c850b798fc13488f1c64'},
 2209: {'batch_count': 61,
        'case_count': 1923,
        'cases_sha256': '6c4a2e0f6ad28ece44a9adc091803f000beab46f09975a49e0089fed108e8093',
        'categories_sha256': '462567b887517650bc1ee2b038f1975b93c4ba10210d64cf8d17b2120f3258c9',
        'git_blob_oid': {'javascript': '0f001d87414f9609e92afa333129dac3a8580727',
                         'python': '678ff93c453a6945976b9531ad143a4144be083a'},
        'oracle_group': 'queue02-subset02',
        'parameters': ['floor', 'numCarpets', 'carpetLen'],
        'source_group': 2,
        'source_sha256': {'javascript': '63f80d30886b23390ca153b1904468347f1e40b3e9c00f88feb4c94c78d67c8c',
                          'python': 'dc7472122b4b45f3b0566d6a7b16263266e3728e55aad417f755cbdaac69f103'},
        'statement_sha256': 'bf7ac9574e0dab1d592ccae9ec1ffc314bb343d0f73917f521abd9f49b37f060'},
 2213: {'batch_count': 146,
        'case_count': 4589,
        'cases_sha256': '47b73eb3842bd02f532c2db3465e5aa76f6fdbefaab41be661c76ba863eadd3b',
        'categories_sha256': '7f482e028a1a01c78c20e15e72ee43595e4f8780bd755ac5117e9531217793c5',
        'git_blob_oid': {'javascript': 'e7f10d49869191c8c226c1003e337c0af9bf6f3a',
                         'python': '474de3bd371043d5f16f0135a9a037550013a786'},
        'oracle_group': 'queue02-subset02',
        'parameters': ['s', 'queryCharacters', 'queryIndices'],
        'source_group': 2,
        'source_sha256': {'javascript': '3fa82fe799cfaee2aebb8da9602921cb68428394da0086894b3518a84d4f0c5b',
                          'python': '3786840656f727f670ff245f756a75a1b8764ffc9d0a0972ce2919a066cb70cc'},
        'statement_sha256': '0e74c2d36fedd54fcd7c2633ea689f497433ad21128cf51455f757d41a0879b9'},
 2245: {'batch_count': 24,
        'case_count': 710,
        'cases_sha256': '50835777184f958a9822daeb9b27dda3deeab0c365bde43f5c916f62877788ca',
        'categories_sha256': '8094933fec9c00b752704f49b50dce71a90f35102df958a33ce2f8c7ae0ca1c8',
        'git_blob_oid': {'javascript': '5f029f760e48169c8dbadfc34199bc4b5f715532',
                         'python': '6a5ad5c62cb79d62c71f4570cc234909e508224a'},
        'oracle_group': 'queue03',
        'parameters': ['grid'],
        'source_group': 3,
        'source_sha256': {'javascript': '1e0e1927c305bd5f58503f9e17b4c18826a855ba04b18654b9c61033d5fe6b0a',
                          'python': '1840d92bb9c763f27f0fa25536ba6522374a066bfa61484ab4512bf0b26d95ff'},
        'statement_sha256': 'fb8b5ee887f7b04b9ab93bba28b40bcf56e2f8ba9d3a71bbfa7b9191a2ed9efd'},
 2271: {'batch_count': 35,
        'case_count': 1105,
        'cases_sha256': '423f5f26612ff9092d36965f3a082a3eb34d40da8593475cfb5f9423ec020e9e',
        'categories_sha256': 'f1b8fe09e0eb44d17eaa4260b8811c1e9b08657d05c6ab8afb71b21334126e21',
        'git_blob_oid': {'javascript': '2275c5c192afb88d1a664f2d9352da6714563f73',
                         'python': 'e38544cc40a60d169803343c658c7d88fda50706'},
        'oracle_group': 'queue03',
        'parameters': ['tiles', 'carpetLen'],
        'source_group': 3,
        'source_sha256': {'javascript': 'f0fff29abfaf177687e774881f0eab393b7cb592f5a6cb07099b18b2827cf2fb',
                          'python': 'd94014e48b18c915489fe23b885f7956b01a56a95ab0f8906b202dffa822ccd2'},
        'statement_sha256': '3af215a73966a52712b2edfba3e275ebc872ba42499c0132fd43b24acc8e60c3'},
 2289: {'batch_count': 38,
        'case_count': 1177,
        'cases_sha256': 'd5039ad46c87aeaee20cb6cb1597b66ca7aabf2b9a9a845f69231db0f66f97a7',
        'categories_sha256': 'e7dd2cdea57c761b2253334258a9c2d307196e05ef6e75b2ec8d27d222bb4db6',
        'git_blob_oid': {'javascript': '3770ba47ba5646700afd8f68e8aa3c8b812ea056',
                         'python': '3ba8414d38ff734a5c820d06b75a87f68d821ad3'},
        'oracle_group': 'queue03',
        'parameters': ['nums'],
        'source_group': 3,
        'source_sha256': {'javascript': 'e4186f3e31ea02419b3a29fd3c8b5c30fedae506b36b032653f190409bd23e4b',
                          'python': 'f74c84cb62a07d3fa33d5929e6d027d5b9e935606bfa3a142f8e9f9a64b33350'},
        'statement_sha256': '997616b966b67ae65b28e119b5c1d09df537c6049148a308f02eea4d818b288c'},
 2301: {'batch_count': 69,
        'case_count': 2192,
        'cases_sha256': 'c31f4d77c1159ad6f87ade1d72fef9d99f5ac5a9d7a3b863d08f37158922e5e4',
        'categories_sha256': '204837c9491fbae1962565cba5c8a1bde280d0bf8f04baa107840bfedc922fd6',
        'git_blob_oid': {'javascript': '2102a1ae0d5d096e16fd89f885973b80b33b5a80',
                         'python': '5c7912099a265872a775b8c1adb2c1e616b530a1'},
        'oracle_group': 'queue03',
        'parameters': ['s', 'sub', 'mappings'],
        'source_group': 3,
        'source_sha256': {'javascript': '4cd98a5c6feaade45515b930c6040826af507e83048576add8ded1f24944af49',
                          'python': 'b1da6139f7c66788b70d63577f5865167c33e7f60b3301e7c469eb6d32e708c8'},
        'statement_sha256': 'effa976688678c569bc6c6f553dee75da67294280cec2f4f20db63edc3373a27'},
 2321: {'batch_count': 15,
        'case_count': 445,
        'cases_sha256': 'fef5d53f3d4414b651533c366af659ccac693fda1f72c0ec6cb4e6d4ee527cd1',
        'categories_sha256': 'bca7ba9f0dda8f674523a590c8bd24d35582e397898132ec7a7dceaf2e15b576',
        'git_blob_oid': {'javascript': '5a9322a3f44b6758e83dd9aba2e7df5cc92b58d1',
                         'python': 'e3b1a6bfa9f0a4c557910bfef963d74e4780d7b8'},
        'oracle_group': 'queue03',
        'parameters': ['nums1', 'nums2'],
        'source_group': 3,
        'source_sha256': {'javascript': 'd16d3585774126954655047e68a4ee92e0d54df2823346ce8753725e8cd45c63',
                          'python': 'ceb8b8ddc64d821b9fc5f23cbecb077f5a893942704bdfb38157f7e1baad95b4'},
        'statement_sha256': 'bb7adb649e2e016a69d91569d306550987a63394154efd9f88e004296522f3f0'},
 2333: {'batch_count': 29,
        'case_count': 841,
        'cases_sha256': '8412de71c8e5716b94f04ee88e8084d1d744e5b4edaf70a5ea664cad80aa1b6f',
        'categories_sha256': '2bc11fb5001065b2cda1da13cd7321cd1ff3e2187631a165ba77fad535004154',
        'git_blob_oid': {'javascript': '23227ea0db962bc3fc866eb43e0b1e31a96d1970',
                         'python': '21298ed62df3430f4e5690c1bb663f3d6a465703'},
        'oracle_group': 'queue03',
        'parameters': ['nums1', 'nums2', 'k1', 'k2'],
        'source_group': 3,
        'source_sha256': {'javascript': '96ea3df11ec5314890504d1d07f1e32ef9fb724e1a51e2a01f454577b9872ecd',
                          'python': '5269fecd6443e768014f00268f083be425f10f8dcec1f5c327d1d38def252edf'},
        'statement_sha256': '065f74e469b25ab5bf499d63170e03a8d6fbd92dcbbe4381590129f25438fd8a'},
 2348: {'batch_count': 37,
        'case_count': 1178,
        'cases_sha256': 'c16ced3d30e371f16274b8f637ae54591e6653c77bd8059167baaea580b2ce51',
        'categories_sha256': 'caf497a21eafe9f696b3db8f0238148dbd5e7e5252b396ab54ee0f6d5c32ba48',
        'git_blob_oid': {'javascript': 'c2a944f9281e836cb4076817fa7418e6dc11bd37',
                         'python': '716b134ae92f827d1c8c1c5f2a27369fb2dd87ed'},
        'oracle_group': 'queue03',
        'parameters': ['nums'],
        'source_group': 3,
        'source_sha256': {'javascript': '8664f11b9ebf082368141505e092429cad157909af8e1537b7bd6da46e7b31c3',
                          'python': '4fe3abbc3f149daf8a52497d61d21d2a08a273d6a309238b724b03556a8fb74d'},
        'statement_sha256': 'cabe0ff21c1e40098bba91e3d4a06962d6f0120cffb754524f4ec06358b57fe7'},
 2375: {'batch_count': 16,
        'batches_sha256': '51d52a8846fa46e5a4fcf204e3360c8fc19e2900d8fc772e3b1b33fec3f07a99',
        'case_count': 512,
        'cases_sha256': '9e506671242e0a7b573149d1f5c135b2f5ccd90e24450f471d52e1371049ea11',
        'categories_sha256': '83c0fcc965f0b8c3fa4cf35a6d37f04de96f8a85525ae72483cd96551828d348',
        'git_blob_oid': {'javascript': '548c194ff9d476f6a1b165d3afee0c60ef6ed3b6',
                         'python': '06a3c4df83a4cf620dec3a6b6e9c43f1716f7266'},
        'oracle_group': 'queue04',
        'parameters': ['pattern'],
        'source_group': 4,
        'source_sha256': {'javascript': '5a5414ca0065c9fb1d342eac75220dcc7e3ff304a52c5ff9df9bf14a07c53564',
                          'python': '1aa773e4034a3483b795114043f971f0afc5c1f1c2a746f899947e7f21351392'},
        'statement_sha256': '4c9fcfe8b47ab7c36d06709689d6c13d92021245b8f695300bbd4a3d5e02ba0f'},
 2384: {'batch_count': 13,
        'batches_sha256': 'dde54d37c0d762861488068960b7e48bdbe46aea20d1b3d36c4918b5261cb2c4',
        'case_count': 410,
        'cases_sha256': '5f349893cd8f27f23e2372341dee69a603082e08feb93eef0e4922884099ca68',
        'categories_sha256': '52253605b043fee1f0507cf55fe8cb650abb404de0aa0ee85f4ddbff6a9338c3',
        'git_blob_oid': {'javascript': 'fe5808398f4bb0eebf103dddc451e360d390db2f',
                         'python': 'b1a8d7cfc82ae1c5051d0309a4656e234fdab883'},
        'oracle_group': 'queue04',
        'parameters': ['num'],
        'source_group': 4,
        'source_sha256': {'javascript': '7d8dde8bf0193c396d766c8b811d671a2e3f48ec1a5bfa23b68ec28086560552',
                          'python': '2f018c160b0a9e241dd3ccbe4aca0e3b54024ca296a3fc5228396c2d6ae649c4'},
        'statement_sha256': 'eb89df8e4fd731e874f6be67851a7ee7207db30ca5125235817ff3cfde8cf06d'},
 2396: {'batch_count': 17,
        'batches_sha256': '2d0b82a25b31e0f84915aecaeb01f7bd3409f3e5f1539f791bcc9545b5fd9f74',
        'case_count': 516,
        'cases_sha256': 'd4db167b5722a11380669deb1ab8d6be4bfa4e4725a67716793bf2e78011c7a5',
        'categories_sha256': 'a3269b8cb723f51478a49c8703078ad7f95cf721185c5d085af6a3ed84ed5a14',
        'git_blob_oid': {'javascript': '4c7a02d39de50a1300376b349c117cc4e09a06e4',
                         'python': '97509f12bc54daadbd3a149738ae6e18f67a01b8'},
        'oracle_group': 'queue04',
        'parameters': ['n'],
        'source_group': 4,
        'source_sha256': {'javascript': '9903c6869b69b2683cc1a28c028a6d85aed6fa296c750a80cf008a0282ec07a6',
                          'python': '802a071223937922571b2f80ff6725fa9ae26a8bba2135c7d4b78a1e427889c9'},
        'statement_sha256': 'b997eb4f1df1a93489459be23a2fd4b7fe750a48ee34857d56d0789fb94542bc'},
 2428: {'batch_count': 19,
        'batches_sha256': '2f1a3e3fd812e585e9be50d269498bf35ce8e9fa489b2007f6ff1e69e6506575',
        'case_count': 597,
        'cases_sha256': '017e774bba92182f86c760215d94b2ea2064c0906c0ef055bf615fcaa78b0472',
        'categories_sha256': 'b2f92f911f4d854d7a82659582dbd9e430baa4323c00312d8d9e1447cfe96d8b',
        'git_blob_oid': {'javascript': 'fd28c11104ea4868aa985e99e7d80b85839d37bd',
                         'python': '4d41aa069068560c8e0f031d2e413fae532e9d15'},
        'oracle_group': 'queue04',
        'parameters': ['grid'],
        'source_group': 4,
        'source_sha256': {'javascript': '4cad43365c85d14eea654a05873e489ed9c0044bb37b413f64eabc8ebea8d39e',
                          'python': 'fe80ab6dbc047d021a27b8549ac2c249815a8cbf35288e6aff2a6d7ac22e653f'},
        'statement_sha256': 'ff99ab08a2e86899d75d5ab39a2a10170bb1e562cb9e27039e6b18e8fcafc5bd'},
 2438: {'batch_count': 10,
        'batches_sha256': '80348296463b8911c573d6ffb2d3a89e5a41eb9f0bbec618265208c4ab3caefe',
        'case_count': 290,
        'cases_sha256': '5d6b26f3ada9fce48af49f74406a52a4e339db41981741affc6d97365ac04eb7',
        'categories_sha256': 'c8f1c9acb9152a79433c572764ad46340cc0a74e83c84e2886b1c1658dd8c29a',
        'git_blob_oid': {'javascript': '25d5fbba9274a23303115b184ac6f972f45775a7',
                         'python': 'd2ce1859269a145bd2c5a1b2643f92992c9d0e79'},
        'oracle_group': 'queue04',
        'parameters': ['n', 'queries'],
        'source_group': 4,
        'source_sha256': {'javascript': '43cc5090c11b825388dfdc09f95e44750203e995fb8300990f77411d7c404d6b',
                          'python': '0bd47354655504ebf47f4b66b92b7fdff9ecc8fd28bf7c324606656cbeeaad18'},
        'statement_sha256': '2d4e4ded304b49033e186905278519240e2ea1488284ba2d9419c06ad4b4c240'},
 2443: {'batch_count': 33,
        'batches_sha256': 'cefee9448c299bacedb6fb252502bfa3daef8ccf69ce3ef795141c640cbce3e0',
        'case_count': 1033,
        'cases_sha256': '6a89f2fb5e45dcfb2e8af773b041b64690b2682741dc4f92ef6cf062c49d71ba',
        'categories_sha256': 'b1e592d49990d29052451cf749def6ed35e739ba058e91526738b10482dbf682',
        'git_blob_oid': {'javascript': 'd90bc883de12ef3a9df760253b6bcd17059908d7',
                         'python': '08e7d131c18abdb0aeb95fd3425fffea6cd8c18c'},
        'oracle_group': 'queue04',
        'parameters': ['num'],
        'source_group': 4,
        'source_sha256': {'javascript': 'dbcb701c295d59bdb16b296d16c905936b5149ff4ca55edb703005e898f1d165',
                          'python': '04218c7e489f7431d2539f7363d69f08b8930b83e1e9462b1ea2e60fcae29092'},
        'statement_sha256': 'd8eab25db7a0f0795ad2d3452b1e830cd9aae933d70826048016b65f5447eeb0'},
 2449: {'batch_count': 16,
        'batches_sha256': 'd45982ee5e2f0736142127994c0548303ba33efdda18843158e6cc2901be52fe',
        'case_count': 505,
        'cases_sha256': '6e4b27d8468127427743dd4642657c6e5b0666db42f07fcd7964a98711fc2fe6',
        'categories_sha256': '44e9dd61e167bdeac511706997fb1d2cff0d0750d2ada966b30aa560a5d4d126',
        'git_blob_oid': {'javascript': '3069ff2897bcadbdd9042e5e276daf085451e503',
                         'python': '142f7f3c3d56a468ddacd512e1b426ddc768a546'},
        'oracle_group': 'queue04',
        'parameters': ['nums', 'target'],
        'source_group': 4,
        'source_sha256': {'javascript': '61e5336773bfbe7f005e60966ccb6e06fcd02f95c57664835804f98c9a7a291c',
                          'python': 'b5a5e0c7ca38ad3ac0c360db14186a608b37d0d141a65c661c424d3ff907fcad'},
        'statement_sha256': '366fb9c78833eb8ca5aca23ef820a76081584226e88034372d0149c06498e534'},
 2452: {'batch_count': 13,
        'batches_sha256': 'fb84e548e499cf23c4e760855c911f747533c46c261a9dadd5009ceee4065507',
        'case_count': 405,
        'cases_sha256': '0f2ccfbfd27c06d2eefb178cb6fd0fc266dd27e30dcde30d10207459e7ef898b',
        'categories_sha256': '60c356aea7916d014a8a14db71f36e5c3453d85165fdec7d301224c5044c162c',
        'git_blob_oid': {'javascript': '9a1829fdabcb5ff3fe29d36bb07bb1f8c77dc882',
                         'python': 'cf6d9dda69d629e4731cbee65e4b374b91c63bee'},
        'oracle_group': 'queue04',
        'parameters': ['queries', 'dictionary'],
        'source_group': 4,
        'source_sha256': {'javascript': 'e747f80d3f926aaa025dd25dddca6813317d6ff60a0c9e3beb72ea4b847a9daf',
                          'python': '14526571c7fa6bb4a2ae01c1cb7023c80ee84643ba7123f9ea7757cd63dd73a2'},
        'statement_sha256': 'c40aa5c1ebf482ada0dd5f981c879e6f8538de928515ce8c379241741f516c04'},
 2467: {'batch_count': 18,
        'batches_sha256': '5a6935d892d84ca93db958ef17882ae36b278f23ac06fced2b900f1f8c259905',
        'case_count': 523,
        'cases_sha256': 'c9e80467b8d6c4e2aca5c578d7b21fa8e3b646a7e03a84d7b9736ae8041e7314',
        'categories_sha256': '3f91d879e7da170a177c22d585a891ce474fd973fe97c587404e4624b2bc4a51',
        'git_blob_oid': {'javascript': '38eadf33d79b98769f42bf32a2a01f1cde9d3539',
                         'python': 'bbf6475563d8fc568a3470e70a59f5915b970e0c'},
        'oracle_group': 'queue04',
        'parameters': ['edges', 'bob', 'amount'],
        'source_group': 4,
        'source_sha256': {'javascript': '7ba8ba27ee94b617f1c877e2b40a5379e3124fa0a422b70dbb48d7d7d38876e7',
                          'python': '695a0440c0daae8fd74caa555ead9194b4d52bd77fb684069c222661d4640016'},
        'statement_sha256': 'f91e0b402ccc6546474acda43599f2adcf5a6a642d2ed902a815c2580c0c1905'},
 2498: {'batch_count': 11,
        'batches_sha256': 'a534806ed40f3cba8d037aa0ec245f09fa4752f78a2778a31a72aef1db9a73e3',
        'case_count': 291,
        'cases_sha256': 'a2a7ab8adb4fd57376d4dba25c8ddda9fc36f2dc4aae47690de449d3e79cfc1a',
        'categories_sha256': '9aaf469bb3c13b0789ac9a6cc2d69c30cb5e8238879a9993354846a25101c777',
        'git_blob_oid': {'javascript': '20834d76741a0a8dd673ecbe0ea7d74f6cf6a51f',
                         'python': 'ca2288aada08a8dbed4468b15851cd4cead99bab'},
        'oracle_group': 'queue04',
        'parameters': ['stones'],
        'source_group': 4,
        'source_sha256': {'javascript': 'f94eda5860ceda536a1e8d0404de03b12906b9d3062b8e81e5edba8e558d25b3',
                          'python': '0a25e1a4cd895166be64eb733cc2020654ebc096dc97b8beb2dff55896b1da1a'},
        'statement_sha256': '2360be9c5315846910d89659eca90e9fb0928da196682a848c0957554abb6efd'}}
ORACLE_SHA256 = {'request_git_queue01_oracles.py': 'bc853c5ebb75633011f3aa66652ac9d69451b40bbbfe7bd2245fc9cac0595fc3',
 'request_git_queue01_subset02_oracles.py': '1a6e869a29f2837a256753ae2e9188b871319356e25e92aa9df16c15aea93de9',
 'request_git_queue02_subset02_oracles.py': 'd22fb059568cef2e179673d822ee45935d22dfe0199b5b559125ba5e0af87716',
 'request_git_queue03_oracles.py': 'b81f307c9f58332b78291a0a6c9a3bb173b15a4b39dccda643788fee3fb90629',
 'request_git_queue04_oracles.py': '873ddb294609feb447b3d978410537c861e782c7119ce06c1ec12b851e611ba8'}
EVIDENCE_SHA256 = {'1943-order-assessment.json': '14548c0c149484f5f1665673a1966ab7921de93e3f18a4b85e8ab5b343ca2769',
 'batch01-acquisition-chronology.json': '2b8cd27b3979354d25502abfbe7016c6e0871d6f019354af33cf9cb0b659aab3',
 'batch01-first-review.json': '4f6ff395fc0a215a07d5ea9d8c0bb0b5bcd95b895badf6ebab0ef096fef696e8',
 'batch01-pre-source-review.json': 'b1ca9773c35c2b2e0d1af223a09228224b5d4458260d462dd588457e7b405499',
 'batch01-pre-source.json': '3671592e2296a3050d95c9b21c34b4f006209bf1add523fa6d7143836c267337',
 'batch01-second-review.json': '791e3021ddc51518d881ea79aeee370e13baab93d90b36b7b90081a09378e84a',
 'batch02-first-review.json': 'c6ab77cd3068d0046dda1dfccad7d355f62417b87b03fb9dc7fb9be4e8629017',
 'batch02-pre-source-review.json': '9c831fe2d13589c76502e926a3605cc8cf2b14a6148e4feaa177e5dafb1bfd1e',
 'batch02-pre-source.json': 'a3e2ec722a89827e710bc18e71f8bf765d748b66ae23368c021f5b691a2c5204',
 'batch02-second-review.json': '1314695aa63a8843c838fd8adde7ef0e4aa7066c74386da8f04d44a34eb74b03',
 'batch03-first-review.json': '46dfda61fcd5988c89d17903469d4ce04ed6a265635a440af4429c348829c01c',
 'batch03-pre-source-review.json': 'd07d6bdf9285dcf2afd1e1bd517ff16a5e1f38026fad068a67977b0ce7e85f68',
 'batch03-pre-source.json': 'dd9c4f25c6d7726452c042513335049c8c35ebda72bbad8703114bf8d408adc9',
 'batch03-second-review.json': '0d67974d7ac82e81ead32c8902b842d65b98d662a73fa6dfe8b14929bd9082be',
 'batch04-first-review.json': '3ceaa72e7e6d40398c1c86d40b9007d40793f9a2b897ba6a82cbe37d463dd0f1',
 'batch04-pre-source-review.json': 'c0b9940036b80fc8d3ac0b1eba344255dee7f6858ec072b317d4cb0f17482606',
 'batch04-pre-source.json': '570473f7285dac7ea10f62d9f18955c78d84913d7fa978b558c619d639aab8ee',
 'batch04-second-review.json': '2e751e269f0b20478367e1ae91af21abbf3fcfb61114636c034659f3620d8782',
 'queue01-manifest.json': '2dc4be75558af26ddecd0ade3bb8bac3bf9bbd84631b0e13af1975267913fee5',
 'queue01-oracle-review.json': 'af62f7ea693c71ef9421588fbf18be3fc057c2e303abfe47adeba93aa26345b8',
 'queue01-subset02-manifest.json': '5823177d2dbb7e3b9fce2a17f06270e44c87ac60e8e69b6e4714e143380b385f',
 'queue01-subset02-oracle-review.json': '38c83463818a9533cf220f6c9cf18ce8b80f261d69001e279d384f62f13d59c3',
 'queue02-subset02-manifest.json': '6d877337eec216c12977f3b5268d39d3d6ac28b8628674aac58235f18f416f4d',
 'queue02-subset02-oracle-review.json': '2560448387b514d44c53c47ac48f88ce21274fe4e3c309c17a0a29f821328911',
 'queue03-manifest.json': 'ca5e08ef95495ab0b6486caed683a5d5aa49d6d6fd69d2679c240c8a08e59b62',
 'queue03-oracle-review.json': 'c2bf52c2156b75ab5f795bedaf4f80c041d2b0ad3ebb8128bd9bb6bfcbf71101',
 'queue04-manifest.json': 'dd9afbce37f31cf63256318d75be06e3de717148a1de938c0e69c9d623f17762',
 'queue04-oracle-review.json': '3c5cddca7e6f9ed16ed308596cd4381435e66d138d2818f75fe2a3ddc9781cef'}
OLD_LOADER_SHA256 = '55ff4173f9dab55de26dcfe502f60b33ecac96fd3ec9689b150cba58daa4b547'
FUNCTION_LOADER_SHA256 = 'b4811fa56db9e34efd62a2543f93f9277ebda90b739b4a2c029bb7e04606635f'
LIMITATIONS = ('Original pre-source interface gaps and batch01/batch04 early source-access chronology remain unchanged; no '
 'restored source blindness.',
 '1943 exact comparison is a post-source stronger convention for these two originals only; public any-order '
 'semantics and generic comparator qualification are unchanged.',
 '1977 and 2245 maximum-shape memory/runtime behavior is unresolved; 2245 JavaScript tall skinny nested '
 'matrices risk the unchanged 64 MiB Node old-space ceiling.',
 'Unchanged MAX_PACKET=1100000 excludes some valid full-domain 2449 and 2467 inputs (compact args examples '
 '1600005 and 1588891 bytes); no dropped frozen cases or cap increase.',
 'Finite frozen cases and two static reviews are not universal proof, full-domain resource qualification, '
 'serving activation or source publication authority.')


def binding(pid):
    if type(pid) is not int or pid not in IDS:
        raise ValueError('problem outside fixed ordinary31 population')
    return BINDINGS[pid]


def oracle_for(pid):
    group = binding(pid)['oracle_group']
    return {'queue01': queue01, 'queue01-subset02': queue01_subset02,
            'queue02-subset02': queue02_subset02, 'queue03': queue03, 'queue04': queue04}[group]


def validate(pid, args):
    oracle_for(pid).validate(pid, args)


def additional_code():
    paths = {str(Path(__file__).resolve()): q.file_hash(__file__)}
    for name, pin in ORACLE_SHA256.items():
        path = Path(__file__).with_name(name)
        if q.file_hash(path) != pin:
            raise ValueError('immutable ordinary31 oracle changed')
        paths[str(path.resolve())] = pin
    return paths


def original_base(config):
    if (config['catalogue']['sha256'] != '9ab963740caad76bb15d602fb2ab93e2d010f2765605a9b9e63bbaa620dbb329' or
            config['verified_receipts']['sha256'] != '63a3c432f5ec3057dda03a560080f089d70ad4fffa9966a215343d61bd2148fc'):
        raise ValueError('original943 qualification base required; prospective adoption base is separate')


def pinned(path, pin):
    raw = q.read(path)
    if q.sha(raw) != pin:
        raise ValueError('fixed evidence changed: ' + Path(path).name)
    return raw


def evidence(root):
    retained = {name: pinned(root / name, pin) for name, pin in EVIDENCE_SHA256.items()}
    for group, ids in SOURCE_GROUPS.items():
        wanted = {(pid, language, BINDINGS[pid]['source_sha256'][language], BINDINGS[pid]['git_blob_oid'][language])
                  for pid in ids for language in LANGUAGES}
        for review in ('first', 'second'):
            value = q.decode(retained[f'batch0{group}-{review}-review.json'])
            rows = value['records' if group in (1, 3) else 'rows']
            observed = [(r['problem_id'], r['language'], r['source_sha256'],
                         r.get('git_blob_oid', r.get('computed_git_blob_oid'))) for r in rows]
            if len(observed) != len(wanted) or set(observed) != wanted:
                raise ValueError('two retained source reviews must bind every exact original')
    return retained


def interface_contract():
    return {'schema': 'gamma.git-ordinary31-interface-successor.v1', 'problem_ids': list(IDS),
            'source_sha256': {str(pid): BINDINGS[pid]['source_sha256'] for pid in IDS},
            'ordered_parameters': {str(pid): BINDINGS[pid]['parameters'] for pid in IDS},
            'prior_pre_source_contract_sha256': {str(g): EVIDENCE_SHA256[f'batch0{g}-pre-source.json'] for g in SOURCE_GROUPS},
            'second_source_review_sha256': {str(g): EVIDENCE_SHA256[f'batch0{g}-second-review.json'] for g in SOURCE_GROUPS},
            'declaration_timing': 'Explicit post-source successor; not retroactive pre-source approval or restored source blindness.',
            'javascript': 'commonjs-function-solve-v1', 'python': 'global-solve-v1',
            'javascript_call': 'Native CommonJS direct callable export; Reflect.apply(exported, undefined, ordered_args)',
            'comparison_policy': 'exact',
            'selected_1943_order': {'source_sha256': BINDINGS[1943]['source_sha256'],
                'assessment_sha256': EVIDENCE_SHA256['1943-order-assessment.json'],
                'stronger_selected_original_contract': 'These two exact originals return minimal painted color-set runs in strictly increasing left-endpoint order; compare untouched rows to already frozen increasing-order expectations.',
                'public_statement_unchanged': 'Any outer row order remains valid under the public statement.',
                'no_normalizer': True, 'generic_any_order_comparator_qualified': False},
            'old_object_loader_sha256': OLD_LOADER_SHA256, 'new_function_loader_sha256': FUNCTION_LOADER_SHA256,
            'original_candidate_bytes_unchanged': True, 'effects_and_domain_unchanged': True,
            'cases_unchanged': True, 'runtime_bounds_unchanged': True, 'automatic_promotion': False,
            'retained_limitations': list(LIMITATIONS)}


def approved_interface(root, review_sha256):
    raw = pinned(root / 'interface-contract.json', q.sha(q.encoded(interface_contract())))
    review_raw = pinned(root / 'interface-review.json', review_sha256)
    review = q.decode(review_raw)
    if (review.get('schema') != 'gamma.git-ordinary31-interface-review.v1' or
            review.get('independent_review') is not True or review.get('approved') is not True or
            not isinstance(review.get('reviewer'), str) or not review['reviewer'].strip() or
            review.get('contract_sha256') != q.sha(raw) or
            review.get('original_candidate_bytes_unchanged') is not True or
            review.get('effects_and_domain_unchanged') is not True or
            review.get('original_pre_source_gaps_preserved') is not True or
            review.get('selected_1943_post_source_order_approved') is not True or
            review.get('old_object_loader_sha256') != OLD_LOADER_SHA256 or
            review.get('new_function_loader_sha256') != FUNCTION_LOADER_SHA256):
        raise ValueError('independent approval of exact ordinary31 post-source successor required')
    if (q.file_hash(q.COMMONJS_HARNESS) != OLD_LOADER_SHA256 or
            q.file_hash(q.COMMONJS_HARNESS.with_name('function-harness.cjs')) != FUNCTION_LOADER_SHA256):
        raise ValueError('reviewed loader bytes changed')
    return raw, review_raw


def frozen_row(pid, retained):
    spec = binding(pid)
    manifest = q.decode(retained[spec['oracle_group'] + '-manifest.json'])
    limits = manifest['limits']
    nested = spec['oracle_group'] in ('queue01', 'queue01-subset02')
    if ((limits['LIMITS'] if nested else limits) != q.LIMITS or
            (limits['MAX_FILE'] if nested else manifest['max_file']) != q.MAX_FILE or
            (limits['MAX_PACKET'] if nested else manifest['max_packet']) != q.MAX_PACKET):
        raise ValueError('original oracle resource bounds differ')
    rows = manifest['problems' if nested else 'records']
    selected = [row for row in rows if row['problem_id'] == pid]
    if len(selected) != 1:
        raise ValueError('fixed oracle row missing or duplicated')
    return selected[0]


def generated(pid, statement, retained):
    spec = binding(pid); oracle = oracle_for(pid)
    if q.sha(statement) != spec['statement_sha256']:
        raise ValueError('exact statement bytes required')
    cases, categories = oracle.build_cases(pid, statement)
    if (len(cases) != spec['case_count'] or q.sha(q.encoded(cases)) != spec['cases_sha256'] or
            q.sha(q.encoded(categories)) != spec['categories_sha256']):
        raise ValueError('immutable oracle case/category design changed')
    groups = []
    for offset, batch in q.batches(cases):
        packet = q.encoded(q.packet(batch))
        group = {'offset': offset, 'count': len(batch), 'packet_bytes': len(packet)}
        if spec['oracle_group'] in ('queue01', 'queue01-subset02'):
            group.update(packet_sha256=q.sha(packet), expected_observation_bytes={
                lang: oracle.expected_observation_bytes(batch, lang) for lang in LANGUAGES})
        elif spec['oracle_group'] == 'queue03':
            projected = []
            for lang in LANGUAGES:
                records = [{'i': i, 'result': c['expected'], 'result_type': q.expected_type(c['expected'], lang),
                            'args_before': c['args'], 'args_after': c['args'], 'alias_edges': []}
                           for i, c in enumerate(batch)]
                projected.append(sum(len(q.encoded(r)) for r in records) + len(q.encoded({'done': len(batch)})) + (lang == 'python'))
            group['projected_output_bytes'] = max(projected)
        elif spec['oracle_group'] == 'queue04':
            group = {'offset': offset, 'calls': len(batch), 'packet_bytes': len(packet), 'packet_sha256': q.sha(packet),
                     'javascript_expected_output_bytes': oracle.expected_observation_bytes(batch, 'javascript'),
                     'python_expected_output_bytes': oracle.expected_observation_bytes(batch, 'python')}
        groups.append(group)
    row = frozen_row(pid, retained)
    if (len(groups) != spec['batch_count'] or
            (q.sha(q.encoded(groups)) != spec['batches_sha256'] if spec['oracle_group'] == 'queue04' else groups != row['batches'])):
        raise ValueError('original frozen batching or observation projection changed')
    for case in cases:
        validate(pid, case['args'])
    return cases, categories


def source_bytes(path, pid, language, gate):
    spec = binding(pid)
    if language not in LANGUAGES:
        raise ValueError('source outside fixed languages')
    authorize_before_open(f'leetcode:{pid}', gate['artifact_paths'], gate['trusted_hashes'], language=language)
    raw = q.read(path, 1024 * 1024)
    if (q.sha(raw) != spec['source_sha256'][language] or
            hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() != spec['git_blob_oid'][language]):
        raise ValueError('exact original Git source binding differs')
    return raw


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
            [(j.get('id'), j.get('language')) for j in jobs] != [(pid, lang) for pid in IDS for lang in LANGUAGES]):
        raise ValueError('fixed ordinary31 job population or bindings differ')
    original_base(q.decode(pinned(contract['service_config'], contract['service_config_sha256'])))
    input_root = contract.get('input_root')
    if not isinstance(input_root, str) or not Path(input_root).is_absolute() or '..' in Path(input_root).parts:
        raise ValueError('explicit original input root required')
    retained = evidence(root / 'evidence')
    approved_interface(root / 'evidence', contract['interface_review_sha256'])
    for pid in IDS:
        authorize_before_open(f'leetcode:{pid}', gate['artifact_paths'], gate['trusted_hashes'], language='python', payload_kind='statement')
        statement = pinned(root / f'statements/{pid}.md', BINDINGS[pid]['statement_sha256'])
        cases, categories = generated(pid, statement, retained)
        if (q.read(root / f'tests/{pid}.json') != q.encoded(cases) or
                q.read(root / f'tests/{pid}.categories.json') != q.encoded(categories)):
            raise ValueError('frozen case payload differs')
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
        raise PermissionError('fixed ordinary31 population is not currently authorized')
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
        authorize_before_open(f'leetcode:{pid}', gate['artifact_paths'], gate['trusted_hashes'], language='python', payload_kind='statement')
        statement = pinned(args.input_root / f'statements/{pid}.md', spec['statement_sha256'])
        cases, categories = generated(pid, statement, retained)
        if (pinned(args.input_root / f'tests/{pid}.json', spec['cases_sha256']) != q.encoded(cases) or
                pinned(args.input_root / f'tests/{pid}.categories.json', spec['categories_sha256']) != q.encoded(categories)):
            raise ValueError('private packet case bytes differ')
        (args.output / f'statements/{pid}.md').write_bytes(statement)
        q.write(args.output / f'tests/{pid}.json', cases); q.write(args.output / f'tests/{pid}.categories.json', categories)
        for lang in LANGUAGES:
            suffix = 'js' if lang == 'javascript' else 'py'; source = args.input_root / f'sources/{pid}.{suffix}'
            raw = source_bytes(source, pid, lang, gate)
            (args.output / f'sources/{pid}.{suffix}').write_bytes(raw)
            jobs.append(make_job(args.output, pid, lang, cases, str(source.resolve())))
    contract = {'schema': 'gamma.imported-independent-execution.v1', 'selected_problem_ids': list(IDS),
                'jobs': jobs, 'pending': [], 'automatic_promotion': False, 'protected_access': False,
                'service_config': str(args.config.resolve()), 'service_config_sha256': args.config_sha256,
                'input_root': str(args.input_root.resolve()), 'runtime': runtime_identity,
                'code': q.code_pins(), 'additional_code': additional_code(), 'limits': q.LIMITS,
                'max_packet_bytes': q.MAX_PACKET, 'interface_review_sha256': args.interface_review_sha256,
                'effects': 'Read-only arguments; exact typed returns; no mutable return/input aliases or external IO.',
                'retained_limitations': list(LIMITATIONS),
                'scope': 'Exposed development finite-case qualification only; not universal proof, full-domain resource qualification, fresh confirmation or catalogue adoption.'}
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
