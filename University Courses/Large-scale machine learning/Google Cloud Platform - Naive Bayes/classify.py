import sys
import pandas as pd
import numpy as np
import re


Train_File_Path = sys.argv[1]
Input_File_Path = sys.argv[2]
Output_File_Path = sys.argv[3]

# shape (27, 108290)
Train_Dataset = pd.read_csv(Train_File_Path)

# vocabulary from header without last element,
# last column is just class probabilities
# length 108290
Vocab = Train_Dataset.columns[:-1].tolist()

# last column
# (27,)
Class_Probs = Train_Dataset['class_prob'].values

# Rows without last column
# shape (27, 108289)
Word_Probs = Train_Dataset.iloc[:, :-1].values.astype(float)


# We will be using sum of logariths instead of multiplication of probs
# so that we will not have underflow problems
# to solve the problem of taking logarith of 0 we will apply smoothing
# so that we clip 
Smoothing = 1e-30
Class_Probs = np.clip(Class_Probs, Smoothing, 1)
Word_Probs = np.clip(Word_Probs, Smoothing, 1)
Opposite_Probs = np.clip(1 - Word_Probs, Smoothing, 1)


def tokenization(text):
    # from document we will match any patterns of letters [a-z], 
    # as suggested we only consider whole document as lowercased 
    # numbers and other symbols we treat as whitespaces
    words = re.findall(r'[a-z]+', text.lower())
    return set(words)

def classification(document):
    Words = tokenization(document)
    
    # Here we are calculating this first formula from first page of the assignment
    # but with applied logariths
    
    # Here is the first expressions
    Class_Scores = np.log(Class_Probs)

    for index, word in enumerate(Vocab):
        
        # here we are going through all words in Vocab
        # if the word is present in the document we got: P(x=1| C_k)
        # else: (1 - P(x=1| C_k)
        # ( Those are expressions from second formula from the assignment)
        # we at the end apply also apply np.log on the particular value that we take
        if word in Words:
            Class_Scores = Class_Scores + np.log(Word_Probs[:, index]) 
        else:
            Class_Scores = Class_Scores + np.log(Opposite_Probs[:, index]) 
            
    return np.argmax(Class_Scores)


with open(Input_File_Path, 'r') as f:
    Documents = f.readlines()

Predictions = [classification(doc) for doc in Documents]

with open(Output_File_Path, 'w') as f:
    for prediction in Predictions:
        f.write(f"{prediction}\n")
