"""One parallel forward over typed operation, edge, binding and literal slots."""
import torch
from torch import nn

from .typed_prediction_codec import OPS, INPUTS, BITS


class TypedPredictor(nn.Module):
    def __init__(self,embedding_dim,slots,type_count,width=64):
        super().__init__()
        self.slots=slots; self.type_count=type_count
        self.project=nn.Linear(embedding_dim,width)
        self.positions=nn.Parameter(torch.randn(slots,width)*.02)
        layer=nn.TransformerEncoderLayer(width,4,dim_feedforward=width*2,dropout=0.,batch_first=True)
        self.encoder=nn.TransformerEncoder(layer,2,enable_nested_tensor=False)
        self.heads=nn.ModuleDict({'op':nn.Linear(width,len(OPS)),
                                 'first':nn.Linear(width,slots+1),'next':nn.Linear(width,slots+1),
                                 'binding':nn.Linear(width,INPUTS+slots),'bits':nn.Linear(width,BITS)})
        self.types=nn.Linear(width,(INPUTS+1)*type_count)

    def forward(self,query,memory):
        slots=self.project(query)[:,None,:]+self.positions[None,:,:]
        state=self.encoder(torch.cat([slots,self.project(memory)],dim=1))[:,:self.slots]
        result={key:head(state) for key,head in self.heads.items()}
        result['types']=self.types(state[:,0]).view(-1,INPUTS+1,self.type_count)
        return result


def per_example_loss(logits,labels):
    """Return one loss per target; callers may minimize over valid alternatives."""
    losses=[]
    for key,predicted in logits.items():
        target=labels[key]; mask=target!=-100
        if key=='bits':
            raw=nn.functional.binary_cross_entropy_with_logits(predicted,target.clamp_min(0).float(),reduction='none')
        else:
            raw=nn.functional.cross_entropy(predicted.reshape(-1,predicted.shape[-1]),target.reshape(-1),
                                             reduction='none',ignore_index=-100).view_as(target)
        masked=(raw*mask).flatten(1).sum(1)/mask.flatten(1).sum(1).clamp_min(1)
        losses.append(masked)
    return torch.stack(losses).sum(0)


def decisions(logits,index=0):
    return {k:((v[index]>=0).long() if k=='bits' else v[index].argmax(-1)).tolist() for k,v in logits.items()}
