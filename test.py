# -*- coding: utf-8 -*-
"""Capstone_Model_build_final.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/14pD79pgPvzlYf7_uY3kLYCvGrCQP5SDr
"""

# from google.colab import drive
# drive.mount('/content/drive')

"""Import statements"""

import math
import os
from torch.utils.data import Dataset
import h5py
import torch

# !pip install transformers

from transformers import (
    AutoConfig,
    AutoModelWithLMHead,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    PreTrainedTokenizer,
    Trainer,
    TrainingArguments,
    set_seed,
    TrainerCallback
)

# from google.colab import drive
# drive.mount('/content/drive')

""" select the GPU to train the model on"""

os.environ["CUDA_VISIBLE_DEVICES"]="0"
# --optional (to debug the cuda error)
os.environ["CUDA_LAUNCH_BLOCKING"]="0"

# train_temp='/content/drive/MyDrive/Projects/Capstone:NRG/Week 5/train_temp.txt'
# test_temp='/content/drive/MyDrive/Projects/Capstone:NRG/Week 5/test_temp.txt'
# cached_features_file='/content/drive/MyDrive/Projects/Capstone:NRG/Week 5/data_temp.h5'

"""PyTorch dataset class """

class H5Dataset(Dataset):
    def __init__(self, tokenizer, file_path='train_temp', block_size=512): 
        cached_features_file = "data_temp.h5"

        # logger.info("Loading features from cached file %s", cached_features_file)
        print(("Loading features from cached file %s", cached_features_file))
        with h5py.File(cached_features_file, 'r') as f:
            if file_path=='test_temp':
                self.samples = f[file_path][:] #this is a dev set, 30% of a test set
            else:
                self.samples = f[file_path][:]

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, item):
        return torch.tensor(self.samples[item])

def get_dataset( tokenizer, evaluate=False, local_rank=-1):
  file_path = "test_temp" if evaluate else "train_temp"
  return H5Dataset(tokenizer=tokenizer, file_path=file_path)

set_seed(20)

"""Transformer configuration"""

config = AutoConfig.from_pretrained('gpt2', cache_dir='cache')

"""Tokenizer for the model training"""

tokenizer = AutoTokenizer.from_pretrained('gpt2', cache_dir= 'cache')

"""Initialising the GPT2 model"""

model = AutoModelWithLMHead.from_pretrained(
            'gpt2', # model name
            config=config,
            cache_dir='cache', # cache directory (path to the cache directory)
        )

"""Adding the sppecial recipe token to the tokenizer"""

special_tokens = {
    "additional_special_tokens": ['<RECIPE_START>',
                                  '<INPUT_START>',
                                  '<NEXT_INPUT>',
                                  '<INPUT_END>',
                                  '<INGR_START>',
                                  '<NEXT_INGR>',
                                  '<INGR_END>',
                                  '<INSTR_START>',
                                  '<NEXT_INSTR>',
                                  '<INSTR_END>',
                                  '<TITLE_START>'
                                  ,'<TITLE_END>'
                                  ,'<RECIPE_END>'
        ]
}

tokenizer.add_special_tokens(special_tokens)
model.resize_token_embeddings(len(tokenizer))  # resizeing the model to fit the tokenizer with special tokens


# converting the train and validation dataset to pytorch Dataset so as it can be given to the model as input for training
train_dataset = ( get_dataset(tokenizer=tokenizer) )
eval_dataset = (  get_dataset(tokenizer=tokenizer, evaluate=True) )

'''
* To be able to build batches, data collators may apply some processing (like padding). Some of them
(like DataCollatorForLanguageModeling) also apply some random data augmentation (like random masking) oin the formed batch.
* Data collators are objects that will form a batch by using a list of dataset elements as input. These elements are of the same type as the elements of train_dataset or eval_dataset.
* Forming the batches to dataset to be trained
source :- Hugginface.co
'''

data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer, mlm=False, mlm_probability=0.15  )

training_args = TrainingArguments(
    
    output_dir= "./outputs",
    
    num_train_epochs=1,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    gradient_accumulation_steps=8,
    evaluation_strategy="steps",
    fp16=True,
    fp16_opt_level='O1',
    warmup_steps=1e2,    
    learning_rate=5e-4,
    adam_epsilon=1e-8,
    weight_decay=0.01,        
    save_total_limit=1,
    load_best_model_at_end=True,     
)

# Initializing our PyTorch Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    data_collator=data_collator,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
)

# saving the tokenizer object 
tokenizer.save_pretrained('./outputs/tempt')
# Starting the Training and saving the model
trainer.train()
trainer.save_model()

# saving the tokenizer after training the mode, just to be safe
tokenizer.save_pretrained('./outputs/tempt')