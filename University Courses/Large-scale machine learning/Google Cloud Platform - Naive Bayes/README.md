# Distributed Naive Bayes Classifier on Google Cloud

## Overview

This project implements a distributed **Bernoulli Naive Bayes classifier** for text classification using **Google Cloud** virtual machines (VMs). The dataset consists of **2 million rows**, where each row contains a **review** and a corresponding **label**. The goal is to efficiently process this large dataset in a distributed manner across multiple VMs, compute word probabilities for each label, and train a classifier.

There are two versions of the training script:
- **`train.py`** and **`train_version_2.py`** differ slightly in how they construct the vocabulary:
  - **`train.py`** removes words that appear only once in the entire dataset (i.e., words that occur in just one document/row).
  - **`train_version_2.py`** also removes words that appear only once across the dataset but **does not remove** words that appear multiple times within the same document.
  
The file **`report.ipynb`** contains analysis and experimental results for the first version (`train.py`).

In the **`VMs Configuration`** folder, you'll find **Terraform configuration files** used to set up the virtual machines (VMs) on Google Cloud.

## Implementation Details

### Training Phase (`train.py` / `train_version_2.py`)

1. **Data Processing**  
   - The dataset is a CSV file with two columns:  
     - **Column 1:** Text (concatenation of the review title and review body)  
     - **Column 2:** Label (integer representing the product category)
   - The vocabulary is created by:
     - Extracting words (continuous alphabetic characters, case-insensitive)
     - Removing words that appear only once across the dataset (with handling differences as explained above)

2. **Distributed Training**  
   - The dataset is divided across multiple VMs.  
   - Each VM processes its share of the dataset to compute:  
     - **P(xi = 1 | Ck)** – the probability that a word appears in a document belonging to class **Ck**  
     - **P(Ck)** – the prior probability of each class  
   - The results are aggregated and saved to a CSV file.

### Classification Phase (`classify.py`)

- The trained model is used to classify new documents.  
- Each document is assigned the class that maximizes the Naive Bayes probability formula.  
- The predicted labels are saved to an output file.



## Running the Code

On the node where the **training script**, **dataset**, and **test files** are located, run the following commands:

### Training:
```bash
mpiexec --hostfile hostfile_mpi -x MASTER_ADDR=<name_of_vm> -x MASTER_PORT=12340 -n <number_of_workers> python3 train.py <dataset_path> <output_path>
```

### Classification:
```bash
python classify.py output.csv <input_path> <output_path>
```