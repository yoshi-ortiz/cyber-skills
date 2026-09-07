---
type: Reference
title: Sentiment analysis
description: A natural-language-processing task that estimates polarity or other sentiment labels from text under a stated scope.
status: stable
resource: https://www.elastic.co/what-is/sentiment-analysis
tags:
  - machine-learning
  - natural-language-processing
  - sentiment-analysis
  - text-classification
generated:
  by: codex/gpt-5
  at: 2026-09-06T00:00:00-06:00
sources:
  - resource: https://www.elastic.co/what-is/sentiment-analysis
    title: What is sentiment analysis?
    author: Elastic
---

# Sentiment analysis

Sentiment analysis is an NLP task that estimates emotional tone or opinion in
text, commonly as positive, neutral, or negative labels or a continuous score.
Elastic describes a pipeline of ingestion, preprocessing, numerical feature
representation, classification, and output scoring. It distinguishes rule-based
lexicon approaches, models trained on labeled data, and hybrid systems. Its
examples also separate broad polarity from finer-grained, aspect-based, emotion,
and intent-oriented tasks.

## Purpose

Use sentiment analysis only after declaring what the label means, at what unit
(document, sentence, aspect, or message), for which language and population,
and what action—if any—may follow an output. Preserve input provenance, model or
lexicon version, prediction score or label, threshold, and uncertainty. Validate
on representative labeled data and inspect failure cases such as negation,
sarcasm, ambiguity, domain vocabulary, and language change.

## Boundary

Sentiment is a prediction about text under a particular representation and
labeling scheme. It is not a verified emotion, intent, demographic attribute,
customer decision, root cause, or authorization for an automated action.
Aspect-based and intent-oriented variants require their own labels and
evaluation; a document-level polarity score cannot establish either. Elastic's
guide is vendor educational material, so treat its use cases as examples rather
than performance guarantees.
