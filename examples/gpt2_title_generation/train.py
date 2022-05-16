import sys

sys.path.append('/data/liuguang/Sailing')
import os
import torch
from torch.utils.data import Dataset
from flagai.auto_model.auto_loader import AutoLoader
from flagai.trainer import Trainer
from flagai.data.collate_utils import seq2seq_collate_fn
from flagai.data.dataset.superglue.control import DEFAULT_METRICS

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# single gpu
trainer = Trainer(
    env_type="pytorch",
    experiment_name="roberta_seq2seq",
    batch_size=1,
    gradient_accumulation_steps=1,
    lr=2e-4,
    weight_decay=1e-3,
    epochs=10,
    log_interval=100,
    eval_interval=10000,
    load_dir=None,
    pytorch_device=device,
    save_dir="checkpoints_seq2seq",
    checkpoint_activations=True,
    save_epoch=1,
)

src_dir = './examples/glm_title_generation/data/train.src'
tgt_dir = './examples/glm_title_generation/data/train.tgt'
model_dir = "./state_dict/"
os.makedirs(model_dir, exist_ok=True)
maxlen = 256

auto_loader = AutoLoader(
    "seq2seq",
    model_name="gpt2_base_chinese",
    model_dir=model_dir,
)
model = auto_loader.get_model()
tokenizer = auto_loader.get_tokenizer()


def read_file():
    src = []
    tgt = []

    with open(src_dir, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            src.append(line.strip('\n').lower())

    with open(tgt_dir, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            tgt.append(line.strip('\n').lower())

    return src, tgt


class BertSeq2seqDataset(Dataset):

    def __init__(self, sents_src, sents_tgt, tokenizer, maxlen=512):
        super(BertSeq2seqDataset, self).__init__()
        self.sents_src = sents_src
        self.sents_tgt = sents_tgt
        self.tokenizer = tokenizer
        self.maxlen = maxlen

    def __getitem__(self, i):
        src = self.sents_src[i]
        tgt = self.sents_tgt[i]
        data = self.tokenizer.encode_plus(src, tgt, max_length=self.maxlen)

        output = {
            "input_ids": torch.LongTensor(data["input_ids"][:-1]),
            "labels": torch.LongTensor(data["input_ids"][1:]),
        }
        return output

    def __len__(self):

        return len(self.sents_src)


sents_src, sents_tgt = read_file()
data_len = len(sents_tgt)
train_size = int(data_len * 0.8)

train_src = sents_src[:train_size][:2000]
train_tgt = sents_tgt[:train_size][:2000]

val_src = sents_src[train_size:]
val_tgt = sents_tgt[train_size:]

train_dataset = BertSeq2seqDataset(train_src,
                                   train_tgt,
                                   tokenizer=tokenizer,
                                   maxlen=maxlen)
val_dataset = BertSeq2seqDataset(val_src,
                                 val_tgt,
                                 tokenizer=tokenizer,
                                 maxlen=maxlen)

trainer.train(model,
              train_dataset=train_dataset,
              valid_dataset=val_dataset,
              metric_methods=[])