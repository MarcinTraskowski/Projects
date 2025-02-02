import sys
import pandas as pd
import numpy as np
import re

import os
import torch.distributed as dist
from collections import defaultdict
import time

start_time_1 = time.time()

# Setting the same as in lab 1
WORLD_SIZE = int(os.environ['OMPI_COMM_WORLD_SIZE'])
RANK = int(os.environ['OMPI_COMM_WORLD_RANK'])
dist.init_process_group("gloo", rank=RANK, world_size=WORLD_SIZE)

Data_File_Path = sys.argv[1]
Output_File_Path = sys.argv[2]


# This variable is for weak scalling,
# it should have values 1/4, 2/4, 3/4 and 1, which is equivalent to strong scalling test
# This could also be passed as a parameter in the command, but I just chose this version
# because assignment says that only those two above should be given
Fraction = 1


# Variables to accuretely distribute rows of the dataset to each node
# Number_Rows is scalled by Fraction if we test weak scalling
Number_Rows = int(sum(1 for _ in open(Data_File_Path)) * Fraction)
Rows_Per_Node = Number_Rows // WORLD_SIZE
Skip_Rows = RANK * Rows_Per_Node

# Necessary if number of rows is not dividable by number of nodes
if RANK != WORLD_SIZE - 1 or Fraction != 1:
    Nrows = Rows_Per_Node
else:
    # None is only for last Node if we take whole dataset
    Nrows = None

Chunk = pd.read_csv(Data_File_Path, header=None, names=['text', 'label'], skiprows=Skip_Rows, nrows=Nrows)

print(f"Rank {RANK}: chunk size: {Chunk.shape}")

# Before checking time, I am adding barrier,
# so that we are sure that all nodes ended particular task
dist.barrier()

if RANK == 0:
    print("Time to distribute data: ",time.time() - start_time_1)

start_time_2 = time.time()

def tokenization(text):
    # from document we will match any patterns of letters [a-z], 
    # as suggested we only consider whole document as lowercased 
    # numbers and other symbols we treat as whitespaces
    words = re.findall(r'[a-z]+', text.lower())
    return words

Chunk['words'] = Chunk['text'].apply(tokenization)


# Here we couldnt simply do sth like Class_Word_Counts = defaultdict(lambda: defaultdict(int))
# because lambda in not pickable and therefore dist.all_gather_object fails
# named function is pickable

def init_nested_default_dict():
    return defaultdict(int)

Class_Word_Counts = defaultdict(init_nested_default_dict)
Class_Counts = defaultdict(int)

# for correcting VOCAB
Word_Counts = defaultdict(int)

# Here we are counting istances of the classes
# and we are counting instances of the word in particular class
for _, row in Chunk.iterrows():
    label = row['label']
    Class_Counts[label] = Class_Counts[label] + 1
    unique_words = set(row['words'])
    for word in unique_words:
        Class_Word_Counts[label][word] = Class_Word_Counts[label][word] + 1
    # for correcting VOCAB
    for word in list(row['words']):
        Word_Counts[word] = Word_Counts[word] + 1

dist.barrier()

if RANK == 0:
    print("Time to train on all vms: ",time.time() - start_time_2)

start_time_3 = time.time()



# Here we want to send all results from nodes to each other

Sync_Class_Word_Counts = [None] * WORLD_SIZE
Sync_Class_Counts = [None] * WORLD_SIZE

# for correcting VOCAB
Sync_Word_Counts = [None] * WORLD_SIZE

dist.all_gather_object(Sync_Class_Word_Counts, Class_Word_Counts)
dist.all_gather_object(Sync_Class_Counts, Class_Counts)

# for correcting VOCAB
dist.all_gather_object(Sync_Word_Counts, Word_Counts)



dist.barrier()

if RANK == 0:
    print("Time to send all results: ",time.time() - start_time_3)

start_time_4 = time.time()


# Now we want to save those results in accordance with the assignment
Merged_Word_label_Counts = defaultdict(init_nested_default_dict)
Merged_Class_Counts = defaultdict(int)

# for correcting VOCAB
Merged_Word_Counts = defaultdict(int)


# Here we are counting instances of a word in particular class (merged results from all nodes)
for node_counts in Sync_Class_Word_Counts:
    for label, word_counts in node_counts.items():
        for word, count in word_counts.items():
            Merged_Word_label_Counts[label][word] = Merged_Word_label_Counts[label][word] + count


# Here we are counting istances of the classes (merged results from all nodes)
for node_counts in Sync_Class_Counts:
    for label, count in node_counts.items():
        Merged_Class_Counts[label] = Merged_Class_Counts[label] + count

# for correcting VOCAB
for word_counts in Sync_Word_Counts:
    for word, count in word_counts.items():
        Merged_Word_Counts[word] = Merged_Word_Counts[word] + count


# Vocabulary
Vocab = set()

# all words
for word_counts in Merged_Word_label_Counts.values():
    Vocab.update(word_counts.keys())
    

# Now we want to sort and delete words that appear only once

# this is not necessary any more because of Merged_Word_Counts
'''
Word_Counter = defaultdict(int)
for word_counts in Merged_Word_label_Counts.values():
    for word in word_counts.keys():
        Word_Counter[word] = Word_Counter[word] + 1
'''
Vocab = sorted([word for word in Vocab if Merged_Word_Counts[word] > 1])

# Class probabilities
Number_Documents = sum(Merged_Class_Counts.values())
Class_Probs = {label: count / Number_Documents for label, count in Merged_Class_Counts.items()}

# this first append is header
Output = []
Output.append(Vocab + ['class_prob'])

# here probabilities (so in the output file it is from second row)
for label in sorted(Merged_Class_Counts.keys()):
    word_probs = [ (Merged_Word_label_Counts[label][word]) / (Merged_Class_Counts[label]) for word in Vocab]
    Output.append(word_probs + [Class_Probs[label]])

# saving the file
Output_DataFrame = pd.DataFrame(Output, columns=Vocab + ['class_prob'])
Output_DataFrame.to_csv(Output_File_Path, index=False, header=False)

dist.barrier()

if RANK == 0:
    print("Time to save all results: ",time.time() - start_time_4)
    print("Final Vocab len:",len(Vocab))
