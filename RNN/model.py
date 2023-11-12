"""
This scripts simply implements the model architecture for text generation using vanilla RNN
"""

# Importing essential libraries
import torch
import torch.nn as nn
import torch.nn.functional as F
import warnings
from tqdm.auto import tqdm
import matplotlib.pyplot as plt
# For type hint
from typing import Tuple, List, Optional
warnings.filterwarnings("ignore")


class RNN(nn.Module):
    """
    Implements a vanilla RNN model using linear layers
    Args:
        in_embd: input c size
        vacab_size: vocabulary size
        h_embd: hidden states embeddings
    """

    def __init__(self, in_embd: int, vocab_size: int, h_embd: int):
        super().__init__()
        self.h_embd = h_embd
        self.x_embd = nn.Embedding(vocab_size, in_embd)

        self.i2h = nn.Linear(in_embd, h_embd)
        self.h2h = nn.Linear(h_embd, h_embd)
        self.h2o = nn.Linear(h_embd, vocab_size)

    def forward(self, x: torch.Tensor, h_prev: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            x: (1, 1)
            h_pred: (1, h_embd)

        Returns:
            h: current hidden state
            out: output
        """
        x_embd = self.x_embd(x)
        h = F.tanh(self.i2h(x_embd) + self.h2h(h_prev))
        out = self.h2o(h)
        return h, out

    def initHidden(self) -> torch.Tensor:
        return torch.zeros(1, self.h_embd)






if __name__ == "__main__":
    print("Running test...")
    from pre_processing import sentencesdataloader
    import logging
    from tokenizers import Tokenizer

    tokenizer = Tokenizer.from_file("tokenizer.json")
    vocab_size = tokenizer.get_vocab_size()
    in_embd, h_embd = 10, 12
    m = RNN(in_embd=in_embd, h_embd=h_embd, vocab_size=vocab_size)

    logging.info(f"Dry running for one example")

    criterion = nn.CrossEntropyLoss()
    optim = torch.optim.AdamW(params=m.parameters(), lr=1e-3)
    losses = []

    for sentences in tqdm(sentencesdataloader):
      for sen in sentences:
        # logging.info(f"sentence: {sen}")
        losses.append(train_rnn(m, sen, tokenizer, criterion, optim))


    plt.plot(range(len(losses)), losses)
        # currently doing character based model

        