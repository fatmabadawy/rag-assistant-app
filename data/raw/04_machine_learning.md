# Machine Learning Fundamentals — Study Notes

## Supervised, Unsupervised and Reinforcement Learning

Supervised learning trains on labelled examples, learning a mapping from inputs
to known outputs; classification predicts a discrete label, regression predicts a
continuous value. Unsupervised learning finds structure in unlabelled data, as in
k-means clustering or principal component analysis. Reinforcement learning trains
an agent through rewards received from interacting with an environment, with no
labelled dataset at all.

## Bias, Variance and Overfitting

Bias is error from wrong assumptions in the model — an underfitting model has
high bias and performs badly on both training and test data. Variance is
sensitivity to the particular training sample — an overfitting model has high
variance, performing well on training data and badly on unseen data. Total
expected error decomposes into bias squared, variance and irreducible noise.
Increasing model capacity lowers bias and raises variance, which is the
bias-variance trade-off.

Practical defences against overfitting include collecting more data,
regularisation, early stopping, dropout in neural networks, and cross-validation
for honest model selection. L1 regularisation adds the absolute value of weights
to the loss and drives some weights exactly to zero, performing feature
selection. L2 regularisation adds the squared magnitude and shrinks weights
smoothly toward zero without eliminating them.

## Train, Validation and Test Splits

The training set fits the parameters. The validation set tunes hyperparameters
and decides when to stop. The test set is touched once, at the end, to estimate
generalisation. Reusing the test set for tuning leaks information and produces an
optimistic estimate that will not hold in production.

K-fold cross-validation splits the data into k parts, trains on k-1 and validates
on the remaining one, rotating k times and averaging. It gives a more stable
estimate than a single split and matters most when data is scarce.

## Evaluation Metrics

Accuracy is the fraction of correct predictions, and it is misleading on
imbalanced data — a model predicting "negative" always scores 99% accuracy on a
dataset that is 99% negative.

Precision is true positives divided by all predicted positives: of the items
flagged, how many were right. Recall is true positives divided by all actual
positives: of the items that should have been flagged, how many were caught. The
F1 score is their harmonic mean, which punishes a model that sacrifices one for
the other.

Which to optimise depends on the cost of each error. Spam filtering favours
precision, because a legitimate email in the spam folder is worse than a spam
email in the inbox. Disease screening favours recall, because a missed case is
worse than a false alarm that a second test will clear.

ROC-AUC measures ranking quality across all thresholds and is threshold
independent. On heavily imbalanced data, precision-recall AUC is the more
informative curve.

## Gradient Descent

Gradient descent minimises a loss function by stepping in the direction of the
negative gradient. The learning rate controls the step size: too large and
training diverges or oscillates, too small and it crawls or stalls in a plateau.

Batch gradient descent computes the gradient over the whole dataset per step,
which is stable but slow. Stochastic gradient descent uses one example per step,
which is fast and noisy. Mini-batch gradient descent, typically with batches of
32 to 256, is the standard compromise and maps well onto GPU parallelism.

Adam combines momentum with per-parameter adaptive learning rates and is the
usual default optimiser for deep networks.

## Embeddings and Semantic Search

An embedding maps text to a dense vector such that semantically similar text
lands close together in the vector space. This is what allows retrieval to match
a question to a passage that answers it without sharing any keywords.

Cosine similarity measures the angle between two vectors and ignores magnitude,
which is what you want for text, where document length should not dominate the
score. If vectors are normalised to unit length, cosine similarity and the dot
product are identical, and Euclidean distance becomes a monotonic function of
cosine similarity.

Approximate nearest neighbour indexes such as HNSW trade a small amount of recall
for a very large speedup, making search over millions of vectors practical.
