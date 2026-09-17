# Evaluation Results

## Metrics

| Metric | Value |
|---|---|
| n questions | 14 |
| retrieval hit rate | 13/14 (93%) |
| answer accuracy | 10/14 (71%) |
| in domain accuracy | 8/12 (67%) |
| refusal accuracy | 2/2 (100%) |

## Per-question results

| # | Question | Retrieved source (top-1) | Answer (truncated) | Correct? | Notes |
|---|---|---|---|---|---|
| q01 | Why do dynamic arrays double their capacity instead of growing by a fixed amount? | 01_data_structures.md | According to [1], dynamic arrays double their capacity instead of growing by a fixed amount because doublin... | PASS | grounded and cited |
| q02 | What is the difference between an AVL tree and a red-black tree? | 01_data_structures.md | According to the CONTEXT, the main difference between an AVL tree and a red-black tree is the balance facto... | FAIL | missing expected content: rotation |
| q03 | At what load factor should a hash table be resized? | 01_data_structures.md | According to the CONTEXT, a hash table should be resized and rehashed when the load factor exceeds roughly ... | PASS | grounded and cited |
| q04 | What is the leftmost prefix rule for composite indexes? | 02_databases.md | The leftmost prefix rule for composite indexes states that a composite index on (a, b) can serve queries fi... | PASS | grounded and cited |
| q05 | Explain the difference between a non-repeatable read and a phantom read. | 02_databases.md | A non-repeatable read occurs when re-reading the same row inside one transaction returns different values b... | PASS | grounded and cited |
| q06 | Why do relational databases use B+ trees rather than hash indexes? | 02_databases.md | Relational databases use B+ trees rather than hash indexes because B+ trees allow for range queries and ord... | FAIL | missing expected content: leaf |
| q07 | What is the difference between flow control and congestion control in TCP? | 03_networking.md | Flow control stops a fast sender from overwhelming a slow receiver, whereas congestion control stops sender... | PASS | grounded and cited |
| q08 | What does HTTP status code 422 mean? | 03_networking.md | According to the CONTEXT, HTTP status code 422 means the request was well-formed but failed validation, whi... | PASS | grounded and cited |
| q09 | When should I optimise for recall instead of precision? | 04_machine_learning.md | According to the CONTEXT, you should optimise for recall instead of precision when the cost of a missed cas... | PASS | grounded and cited |
| q10 | Why is cosine similarity preferred over Euclidean distance for text embeddings? | 04_machine_learning.md | Cosine similarity is preferred over Euclidean distance for text embeddings because it ignores magnitude, wh... | FAIL | missing expected content: angle |
| q11 | What four conditions are required for deadlock? | 05_operating_systems.md | According to the CONTEXT, the four conditions required for deadlock are:  1. Mutual exclusion 2. Hold and w... | PASS | grounded and cited |
| q12 | What is Belady's anomaly? | 02_databases.md | I don't have anything in the indexed documents that answers that. | FAIL | refused a question the corpus does answer |
| q13 | What is the current share price of Apple? | _(none above floor)_ | I don't have anything in the indexed documents that answers that. Try rephrasing, or ask about a topic cove... | PASS | correctly refused |
| q14 | Write me a Python function that reverses a string. | _(none above floor)_ | I don't have anything in the indexed documents that answers that. Try rephrasing, or ask about a topic cove... | PASS | correctly refused |
