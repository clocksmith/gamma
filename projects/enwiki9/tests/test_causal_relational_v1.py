"""Exact rational and native synthetic tests; no corpus execution."""
from fractions import Fraction
from pathlib import Path
import random
import subprocess
import pytest
ROOT=Path(__file__).resolve().parents[1]
Q=1<<48

@pytest.fixture(scope='module')
def binary(tmp_path_factory):
    dest=tmp_path_factory.mktemp('relational')/'fixture'
    subprocess.run(['g++','-std=c++17','-O1','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all','-I',str(ROOT/'lib'),str(ROOT/'tests/causal_relational_fixture.cpp'),'-o',str(dest)],check=True,timeout=60)
    return dest

def test_causal_native_state(binary):
    subprocess.run([str(binary)],check=True,timeout=30,capture_output=True)

def test_integer_update_against_exact_reference(binary):
    rng=random.Random(923);rows=[];expected=[]
    for _ in range(300):
        cuts=sorted(rng.sample(range(1,Q),3));w=[b-a for a,b in zip([0]+cuts,cuts+[Q])]
        p=[rng.randrange(1,65536) for _ in w];truth=rng.randrange(2)
        products=[x*(v if truth else 65536-v) for x,v in zip(w,p)]
        ideal=[Fraction(v,sum(products)) for v in products]
        scaled=[v*(Q-4) for v in ideal];post=[1+v.numerator//v.denominator for v in scaled]
        order=sorted(range(4),key=lambda i:(-(scaled[i]-int(scaled[i])),i))
        for i in order[:Q-sum(post)]:post[i]+=1
        assert all(abs(Fraction(v,Q)-target)<=Fraction(4,Q) for v,target in zip(post,ideal))
        prediction=(sum(x*v for x,v in zip(w,p))+Q//2)//Q
        rows.append(' '.join(map(str,[*w,*p,truth])));expected.append([prediction,*post])
    output=subprocess.run([str(binary),'kernel'],input='\n'.join(rows)+'\n',text=True,capture_output=True,check=True,timeout=10)
    assert [list(map(int,row.split())) for row in output.stdout.splitlines()]==expected

def test_exact_shared_binding_and_permutation_control():
    # Sixteen distinct donors, three predetermined noiseless mentions.
    prior=Fraction(1,16);shared=prior;independent=prior**3
    assert shared/independent==256  # eight ideal bits, with selection priced
    emissions=[Fraction(i+1,136) for i in range(16)]
    assert sum(prior*p for p in emissions)==sum(prior*p for p in reversed(emissions))
    # Whole-sequence Bayesian mixture bound is exact, not a rounded coder claim.
    p=Fraction(1,1000);q=Fraction(1,9);m=(p+q)/2
    assert m>=p/2 and m>=q/2
