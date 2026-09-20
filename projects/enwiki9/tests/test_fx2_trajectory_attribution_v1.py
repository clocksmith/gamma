"""Prospective mask, next-token alignment, disjoint costs and observation timing."""
import struct
import subprocess
from pathlib import Path
import sys
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from gamma_enwiki9.adapters.fx2_training_capture import expected_rows
from gamma_enwiki9.adapters.fx2_trajectory_costs_v1 import analyze, differences, target_mask
from gamma_enwiki9.adapters.fx2_trajectory_native_v1 import adapt


def fixture(path, trained_probability=.5):
    modeled=bytes([7])+b'a'*700
    tokens=expected_rows(b'\x80\0\0\0\0\x07'+len(modeled).to_bytes(4,'big')+modeled,len(modeled))
    selected=target_mask(tokens,[0])
    bits=b''.join(struct.pack('<HB',32768,(c>>j)&1) for c in modeled for j in range(7,-1,-1))
    neural=b''.join(struct.pack('<QBBBBf',i,tokens[2*i],tokens[2*i+1],int(i>0),0,
                    0 if i==0 else trained_probability if i in selected else .5) for i in range(len(modeled)))
    for suffix,data in [('.tokens',tokens),('.bits',bits),('.neural',neural)]:
        Path(str(path)+suffix).write_bytes(data)
    return tokens


def test_next_target_mask_and_complete_cost_partition(tmp_path):
    tokens=fixture(tmp_path/'P');fixture(tmp_path/'A',.25)
    assert target_mask(tokens,[0])==set(range(513,641))
    p=analyze(tmp_path/'P',tokens,[0],701);a=analyze(tmp_path/'A',tokens,[0],701)
    assert p['partitions']['trained']=={'targets':128,'coded_bits':1024,'neural_bits':128.,'final_bits':1024.}
    assert p['partitions']['no_neural']['targets']==1
    assert p['partitions']['no_neural']['neural_bits'] is None
    assert p['total']['neural_targets']==700
    assert p['total']['final_bits']==701*8
    d=differences({'P':p,'A':a},{'P':100,'A':103})['A']
    assert d['partitions']['trained']['delta_neural_bits']==128
    assert d['partitions']['total']['delta_final_bits']==0
    assert d['coding_residual_bits']==24


def test_reject_shifted_truth_or_invented_reset(tmp_path):
    tokens=fixture(tmp_path/'P')
    with pytest.raises(ValueError):target_mask(tokens,[1])
    with pytest.raises(ValueError):target_mask(tokens,[0,0])
    damaged=bytearray(tokens);damaged[1101]=2;damaged[1103]=1
    with pytest.raises(ValueError):target_mask(bytes(damaged),[0])
    p=tmp_path/'P.neural';d=bytearray(p.read_bytes());d[16+8]^=1;p.write_bytes(d)
    with pytest.raises(ValueError,match='alignment'):analyze(tmp_path/'P',tokens,[0],701)


def test_coder_coordinate_validation(tmp_path):
    tokens=fixture(tmp_path/'P');p=tmp_path/'P.bits';data=bytearray(p.read_bytes());data[2]^=1;p.write_bytes(data)
    with pytest.raises(ValueError,match='coordinate'):analyze(tmp_path/'P',tokens,[0],701)


def test_observer_native_timing_and_reset(tmp_path):
    binary=tmp_path/'fixture'
    subprocess.run(['g++','-std=c++17','-O1','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all',
                    str(ROOT/'tests/trajectory_capture_fixture_v1.cpp'),'-o',str(binary)],check=True,timeout=60)
    prefix=tmp_path/'observed';subprocess.run([str(binary),str(prefix)],check=True,timeout=10)
    rows=list(struct.iter_unpack('<QBBBBf',Path(str(prefix)+'.neural').read_bytes()))
    assert rows==[(0,0,1,0,0,0.),(1,1,2,1,0,.25),(2,2,1,0,0,0.)]
    assert len(Path(str(prefix)+'.bits').read_bytes())==3*8*3
    assert len(Path(str(prefix)+'.priors').read_bytes())==3*410


def test_native_adapter_anchors_are_unique():
    members,receipt=adapt(ROOT/'results/fx2_expert_release250k_v3/P-source.zip',
                          ROOT/'src/gamma_enwiki9/adapters/fx2_trajectory_capture_v1.hpp')
    assert len(receipt)==5
    assert members['src/predictor.cpp'].count(b'gamma_trajectory::row(')==1
    assert members['src/coder/encoder.cpp'].count(b'gamma_trajectory::bit(p, bit);')==1
    assert members['src/coder/decoder.cpp'].count(b'gamma_trajectory::bit(p, bit);')==1
