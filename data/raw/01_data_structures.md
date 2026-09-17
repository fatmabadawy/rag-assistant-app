# Data Structures — Study Notes

## Arrays and Dynamic Arrays

A static array stores elements in one contiguous block of memory. Because the
address of element i is computed as base_address + i * element_size, indexing is
a constant-time operation, O(1). The cost of that speed is rigidity: the size is
fixed at allocation time.

A dynamic array (Python's list, C++'s std::vector, Java's ArrayList) wraps a
static array and grows it when it fills up. The standard growth policy is to
double the capacity. Doubling gives an amortised append cost of O(1): copying is
expensive when it happens, but it happens rarely enough that the average cost per
append across n appends stays constant. Growing by a fixed number of slots
instead of doubling would give an amortised cost of O(n) per append, which is why
no mainstream implementation does it.

## Linked Lists

A singly linked list stores each element in a node holding a value and a pointer
to the next node. Insertion and deletion at a known position cost O(1) because
only pointers are rewired, with no shifting of elements. The trade-off is that
random access costs O(n): reaching element i requires walking i pointers from the
head. Linked lists also have poor cache locality, since nodes are scattered
across the heap rather than sitting in one contiguous block. In practice this
makes an array faster than a linked list for traversal even though both are O(n).

A doubly linked list adds a previous pointer to each node, allowing backward
traversal and O(1) deletion given only a reference to the node itself.

## Hash Tables

A hash table maps keys to buckets using a hash function. Average-case lookup,
insertion and deletion are all O(1). Worst case degrades to O(n) when every key
collides into the same bucket.

Two collision resolution strategies dominate. Separate chaining stores a
secondary structure, usually a linked list, in each bucket. Open addressing keeps
everything in the main array and probes for the next free slot; linear probing
checks the next slot, quadratic probing checks increasing square offsets, and
double hashing uses a second hash function to choose the step size.

The load factor is the ratio of stored elements to buckets. Most implementations
resize and rehash when the load factor exceeds roughly 0.75, because probe
sequences grow sharply beyond that point.

## Binary Search Trees and Balancing

A binary search tree keeps every left descendant smaller than its node and every
right descendant larger. Search, insert and delete are O(h) where h is the tree
height. For a balanced tree h is O(log n), but inserting already-sorted data into
a plain BST produces a degenerate tree with h equal to n, collapsing performance
to that of a linked list.

Self-balancing trees fix this. An AVL tree keeps the height difference between
any node's subtrees within one, giving stricter balance and therefore faster
lookups, at the cost of more rotations during insertion. A red-black tree allows
looser balance — the longest path is at most twice the shortest — which makes
insertion and deletion cheaper. This is why red-black trees back most standard
library ordered maps, while AVL trees suit read-heavy workloads.

## Heaps and Priority Queues

A binary heap is a complete binary tree stored in an array, where each parent
compares favourably to its children. In a min-heap the smallest element sits at
the root, so finding the minimum is O(1). Insertion and extraction are O(log n)
because an element bubbles up or sifts down at most the height of the tree.

Building a heap from an unsorted array of n elements takes O(n), not O(n log n).
The standard proof relies on the fact that most nodes sit near the leaves and
therefore sift down only a short distance.

## Graphs

Graphs are stored as an adjacency matrix or an adjacency list. An adjacency
matrix uses O(V^2) space and answers "is there an edge between u and v" in O(1),
which suits dense graphs. An adjacency list uses O(V + E) space and is the right
choice for sparse graphs, which describes most real-world graphs.

Breadth-first search explores level by level using a queue and finds the shortest
path in an unweighted graph. Depth-first search follows one path as deep as
possible using a stack or recursion, and underpins cycle detection and
topological sorting. Both run in O(V + E) on an adjacency list.
