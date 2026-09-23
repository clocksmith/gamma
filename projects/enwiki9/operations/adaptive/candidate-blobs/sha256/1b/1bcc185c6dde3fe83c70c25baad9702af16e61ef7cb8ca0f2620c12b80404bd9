"""Distribution preservation, overlapping masks, and deployed selection checks."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import pytest
import torch
from gamma_enwiki9.adapters.fx2_coverage_preservation_v1 import distribution_kl,target_sets,partition_name,ARMS
from gamma_enwiki9.adapters.fx2_coverage_gate_v1 import select


def test_full_distribution_changes_even_when_truth_probability_matches():
    teacher=torch.full((2,205),.5/204,dtype=torch.float64);teacher[:,0]=.5
    child=teacher.clone();child[:,1]*=1.5;child[:,2]*=.5;child.requires_grad_()
    before=teacher.clone();value=distribution_kl(child,teacher)
    assert torch.equal(child[:,0],teacher[:,0]) and value>0
    value.backward()
    assert child.grad[:,1:].abs().max()>0 and teacher.grad is None
    assert torch.equal(before,teacher)


def test_identity_distribution_has_zero_penalty_and_gradient():
    parent=torch.softmax(torch.arange(205,dtype=torch.float64)/100,0).repeat(2,1)
    child=parent.clone().requires_grad_();value=distribution_kl(child,parent)
    assert value.item()==0;value.backward();assert child.grad.abs().max()<1e-12
    with pytest.raises(ValueError,match='frozen'):distribution_kl(child,parent.requires_grad_())


def test_invalid_or_incomplete_distribution_fails():
    with pytest.raises(ValueError,match='vocabulary'):distribution_kl(torch.ones(2,1),torch.ones(2,1))
    p=torch.ones(2,205)/205;q=p.clone();q[0,1]=float('nan')
    with pytest.raises(ValueError,match='invalid'):distribution_kl(q,p)
    with pytest.raises(ValueError,match='normalization'):distribution_kl(p*2,p)


def test_masks_are_disjoint_intersections_with_explicit_overlap():
    t={'warmup_tokens':512,'loss_tokens':128,'narrow_starts':[0,2611,39712,68859],
       'broad_starts':[0,2611,39712,68859,74848,96984,121722,135975],
       'preservation_starts':[0,2611,39712,68859,74848,96984,106827,121722,135975]}
    masks=target_sets({'training':t});assert {k:len(v) for k,v in masks.items()}=={'narrow':512,'broad':1024,'preservation':1152}
    bins={}
    for i in set.union(*masks.values()):
        name=partition_name(i,True,masks);bins[name]=bins.get(name,0)+1
    assert bins=={'111':512,'011':512,'001':128}
    assert partition_name(1,True,masks)=='000' and partition_name(0,False,masks)=='no_neural'
    with pytest.raises(ValueError):partition_name(513,False,masks)
    for key in ('narrow','broad'):
        schedule=[t[key+'_starts'][i%len(t[key+'_starts'])] for i in range(16)]
        assert 128*len(schedule)==2048
        assert set(schedule.count(v) for v in set(schedule))==({4} if key=='narrow' else {2})


def test_selection_retains_P_for_payload_regressions_despite_smaller_models():
    d={'P':{'archive_bytes':100,'component_bytes':1000}}
    d.update({a:{'archive_bytes':101,'component_bytes':900} for a in ARMS})
    assert select(d)==('P',[])
    d['N']={'archive_bytes':99,'component_bytes':1001};assert select(d)==('P',[])
    d['B']={'archive_bytes':99,'component_bytes':999};d['BR']={'archive_bytes':98,'component_bytes':999}
    assert select(d)==('B',['B','BR'])
