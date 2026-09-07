---
type: Reference
title: Supervised text classification with PyTorch
description: A labeled-text pipeline that maps input messages to predefined classes and evaluates predictions on held-out examples.
status: stable
resource: https://www.ibm.com/think/tutorials/text-classification-pytorch#88312263
tags:
  - machine-learning
  - natural-language-processing
  - text-classification
  - supervised-learning
  - pytorch
generated:
  by: codex/gpt-5
  at: 2026-09-06T00:00:00-06:00
sources:
  - resource: https://www.ibm.com/think/tutorials/text-classification-pytorch#88312263
    title: Build a spam text classifier by using PyTorch
    author: IBM
  - resource: https://docs.pytorch.org/docs/stable/data.html
    title: PyTorch data loading
    author: PyTorch
---

# Supervised text classification with PyTorch

Text classification assigns predefined labels to text. IBM's tutorial makes the
task concrete with binary `spam` and `not_spam` labels: normalize text, tokenize
it, build a vocabulary with padding and unknown-token handling, encode each
message to a fixed length, train on labeled examples, and evaluate on a separate
test set. Its example uses an embedding layer, an LSTM, a linear output, sigmoid
activation, binary cross-entropy loss, and an explicit classification threshold.

## Purpose

Use supervised text classification when a decision has a defined label scheme,
labeled examples representative of the intended use, and a held-out evaluation
set. Record the label definitions, source and split of data, preprocessing and
vocabulary versions, model and threshold, class distribution, and the metrics
that match the error costs. PyTorch's dataset and data-loader abstractions supply
indexed or iterable samples and batched iteration; they do not define label
quality or evaluation validity.

## Boundary

The IBM notebook is a binary spam tutorial, not a general architecture or
deployment prescription. Its reported accuracy is tied to its dataset, split,
preprocessing, class balance, threshold, and experiment. Accuracy alone can hide
costly false positives or false negatives; inspect class-aware measures such as
precision, recall, and F1 when their error trade-off matters. Re-evaluate after
the input source, language, population, labels, or operating threshold changes.
