# Findings: supervised text classification and sentiment analysis

## Scope and source quality

This note synthesizes the two supplied first-party educational sources. IBM owns
the tutorial and its example implementation; Elastic owns the explanation of
sentiment-analysis approaches. They are useful implementation guidance, not
independent evidence that a particular model is safe, fair, or fit for a new
domain.

Sources:

- [IBM: Build a spam text classifier by using PyTorch](https://www.ibm.com/think/tutorials/text-classification-pytorch#88312263)
- [Elastic: What is sentiment analysis?](https://www.elastic.co/what-is/sentiment-analysis)

## Supervised text classification: the IBM spam example

- **Task and inputs.** Text classification assigns predefined labels to text.
  IBM's example uses a prepartitioned dataset with `text` and `label` columns,
  where labels are `spam` and `not_spam`.
- **Representation.** The tutorial lowercases text, removes non-alphanumeric
  characters and NLTK stopwords, maps labels to `1`/`0`, tokenizes text, and
  constructs a vocabulary with padding and unknown-token entries. It encodes
  each message to a fixed maximum length of 50 token IDs.
- **Model and output.** The demonstrated PyTorch classifier combines an
  embedding layer, LSTM, linear layer, and sigmoid; it returns a score that is
  thresholded at 0.5 to yield the binary spam/not-spam prediction.
- **Training and evaluation.** It trains with binary cross-entropy and Adam
  for five epochs, then evaluates on the held-out test partition. The shown
  evaluation computes accuracy; IBM also names precision, recall, F1, ROC, and
  AUC as relevant measures for supervised classification.
- **Boundary.** The reported accuracy is specific to this dataset, split,
  preprocessing, threshold, and run. It does not establish false-positive
  cost, robustness to adversarial or novel spam, privacy handling, production
  serving, or suitability for a different message population. IBM explicitly
  excludes deployment concerns such as serving, API design, scalability, and
  security from the tutorial.

## Sentiment analysis: the Elastic overview

- **Task and inputs.** Sentiment analysis is an NLP task aimed at detecting
  emotional tone or opinion in text. Elastic describes inputs such as emails,
  tickets, chats, social posts, and reviews.
- **Output.** The output may be a polarity label (positive, neutral, or
  negative) or a continuous score, for example from -1 to +1. Variants include
  fine-grained polarity, aspect-based sentiment, emotion detection, and
  intent-oriented analysis.
- **Approaches.** Elastic distinguishes rule-based methods (lexicons and
  hand-authored linguistic rules), machine-learning methods trained on labeled
  text, and hybrid systems. It describes preprocessing and numeric features
  such as TF-IDF, embeddings, and contextual vectors for ML approaches.
- **Evaluation.** The source names accuracy, precision, and recall for model
  performance. Evaluation must be aligned to the selected task: an
  aspect-based model needs aspect-level labels and checks, whereas a document
  polarity model does not prove aspect-level quality.
- **Boundary.** Sentiment is not ground truth about a person, customer intent,
  or product quality. Elastic notes that lexicon methods can struggle with
  sarcasm, contextual meaning, and changing language; ML methods require
  suitably labeled data and training resources. Outputs should therefore be
  treated as scored signals for review or aggregate analysis, with domain and
  language validation before consequential use.

## The distinction

Sentiment analysis can be implemented as a *particular* text-classification
problem when a model learns labels such as positive/neutral/negative. It is not
synonymous with general supervised text classification:

| Dimension | Spam classifier | Sentiment analysis |
| --- | --- | --- |
| Label meaning | Unwanted vs. wanted message | Tone, polarity, emotion, or sentiment toward an aspect |
| Target inference | Whether a message meets a spam-label definition | How language expresses opinion/emotion under a chosen schema |
| Example decision | Filter, quarantine, or route a message | Aggregate feedback or surface text for a reviewer |
| Essential validation | Error rates by message type and the false-positive/false-negative cost | Agreement with labeled sentiment schema across domains, aspects, language, and context |

Both require a defined label schema, representative data, a held-out evaluation
strategy, and monitoring for drift. A high aggregate score from either task
does not justify reusing it for the other: spam labels do not train sentiment,
and general polarity does not determine spam.
