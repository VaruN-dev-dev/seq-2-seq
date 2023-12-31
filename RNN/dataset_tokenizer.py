
"""
This script will do the follwing:
1. Load the dataset with specified rows
2. Build/Train a byteBPE tokenizer for the dataset
3. Save the tokenizer
"""

# Essential Libraries
from datasets import load_dataset
from torch.utils.data import DataLoader, Dataset
import yaml
import warnings
from pathlib import Path
import logging
import os
import sys

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO)


# Loading parameters
# Configuration file
try:
    config_path = Path(__file__).parent / "default_config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
except Exception as e:
    logging.error(f"Error loading configuration file: {e}")
    sys.exit(1)

# Loading necessary things from the config file
BATCH_SIZE = config["BATCH_SIZE"]
NUM_SENTENCES = config["NUM_SENTENCES"]


class SentencesDataset(Dataset):
    def __init__(self, split="train"):
        try:
            self.rawdata = load_dataset(
                "bookcorpus", split=split, streaming=True)
        except Exception as e:
            logging.error(f"Error loading dataset: {e}")
            sys.exit(1)
        self.new_data = list()
        self._make_new_dataset()

    def __len__(self):
        return len(self.new_data)

    def __getitem__(self, idx):
        return self.new_data[idx]

    def _clean(self, sentences):
        """
        Extracts the text part of the sentences in the dataset.
        """
        out = list()
        for sentence in sentences:
            text = sentence["text"]
            text = text.replace("`", '')
            text = text.replace(".", '')
            out.append(text)  # list of sentences
        return out

    def _make_new_dataset(self):
        """
        Makes new dataset from the given dataset.
        The dataset was really huge, and we only need some sentences.
        """
        temp_dataloader = DataLoader(
            self.rawdata, batch_size=BATCH_SIZE, collate_fn=self._clean)
        dataset_size = NUM_SENTENCES // BATCH_SIZE

        for sentences in temp_dataloader:
            self.new_data.extend(sentences)
            dataset_size -= 1
            if dataset_size == 0:
                break


sentencesdataset = SentencesDataset()
sentencesdataloader = DataLoader(
    sentencesdataset, batch_size=BATCH_SIZE, shuffle=True)
logging.info(f"Dataset loaded with {len(sentencesdataset)} sentences")

# Now training the tokenizer
if __name__ == "__main__":
    # Function to yield sentences from dataloader
    def dataloader_sentences_generator(dataloader):
        for batch in dataloader:
            for sentence in batch:  # each batch is a list of sentences
                yield sentence

    from tokenizers import ByteLevelBPETokenizer
    from tokenizers import ByteLevelBPETokenizer
    from tokenizers.processors import BertProcessing

    special_tokens = ["[START]", "[END]", "[SEP]", "[PAD]"]

    logging.info(f"Starting training tokenizer")
    tokenizer = ByteLevelBPETokenizer()
    tokenizer.train_from_iterator(dataloader_sentences_generator(sentencesdataloader),
                                  # vocab_size=52000, not needed here :)
                                  min_frequency=2,
                                  special_tokens=special_tokens)
    tokenizer._tokenizer.post_processor = BertProcessing(
        sep=("[SEP]", tokenizer.token_to_id("[SEP]")),
        cls=("[START]", tokenizer.token_to_id("[START]")),
    )
    original_encode = tokenizer.encode

    def encode_with_end_token(text):
        encoded = original_encode(text)
        encoded.ids.append(tokenizer.token_to_id("[END]"))
        encoded.type_ids.append(0)
        encoded.tokens.append("[END]")
        encoded.offsets.append((0, 0))
        encoded.attention_mask.append(1)
        encoded.special_tokens_mask.append(1)
        return encoded

    tokenizer.encode = encode_with_end_token
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the absolute path of the byteBPE.json file
    tokenizer_path = os.path.join(script_dir, 'byteBPE.json')

    tokenizer.save(tokenizer_path)
