# Database Systems — Study Notes

## The Relational Model

A relation is a table of tuples over a fixed set of attributes. A primary key is
an attribute or set of attributes that uniquely identifies each row; it cannot be
null and cannot repeat. A foreign key is an attribute in one table that
references the primary key of another, and it is the mechanism that enforces
referential integrity — the database rejects a row whose foreign key points at a
non-existent parent.

## Normalisation

Normalisation removes redundancy that would otherwise allow the same fact to be
stored in two places and drift out of sync.

First normal form requires every attribute to hold a single atomic value; no
lists or repeating groups in a column. Second normal form additionally requires
that every non-key attribute depends on the whole primary key, not just part of
it — this only bites when the key is composite. Third normal form additionally
requires that no non-key attribute depends on another non-key attribute, which
removes transitive dependencies. Boyce-Codd normal form is a stricter version of
third normal form: every determinant must be a candidate key.

Denormalisation is the deliberate reintroduction of redundancy to avoid expensive
joins on read-heavy workloads. It trades write complexity and integrity risk for
read speed, and should be a measured decision rather than a default.

## ACID Properties

Atomicity means a transaction either commits entirely or has no effect at all.
Consistency means a transaction moves the database from one valid state to
another, respecting all declared constraints. Isolation means concurrent
transactions do not observe each other's intermediate state. Durability means
once a transaction commits, its effects survive a crash, normally guaranteed by a
write-ahead log flushed to disk before the commit is acknowledged.

## Isolation Levels and Anomalies

Three classic anomalies define the isolation levels. A dirty read occurs when a
transaction reads data written by another transaction that has not yet committed.
A non-repeatable read occurs when re-reading the same row inside one transaction
returns different values because another transaction committed an update between
the reads. A phantom read occurs when re-running the same query returns a
different set of rows because another transaction inserted or deleted rows
matching the predicate.

Read Uncommitted permits all three. Read Committed prevents dirty reads.
Repeatable Read additionally prevents non-repeatable reads. Serializable prevents
all three and is equivalent to executing transactions one after another. Stronger
isolation costs concurrency, so most production systems default to Read Committed
or Repeatable Read rather than Serializable.

## Indexing

An index is a secondary structure that speeds up lookups at the cost of extra
storage and slower writes, since every insert and update must also maintain the
index.

The B+ tree is the default index structure in relational databases. All data
pointers live in the leaf nodes, and the leaves are linked together, which makes
range queries efficient — find the start of the range, then walk the leaf chain.
Internal nodes hold only keys, so a high branching factor keeps the tree shallow
and the number of disk reads low, typically three or four for millions of rows.

A hash index gives faster exact-match lookup but cannot serve range queries or
ordered scans at all, because hashing destroys key ordering.

A composite index on (a, b) can serve queries filtering on a alone or on a and b
together, but not on b alone. This is the leftmost prefix rule, and it is the
most common reason an index that "should" be used is ignored by the planner.

A covering index contains every column a query needs, letting the database answer
from the index alone without touching the table. This is called an index-only
scan.

## Joins

A nested loop join scans the outer table and probes the inner table for each row;
it is efficient when the outer table is small and the inner side is indexed. A
hash join builds a hash table on the smaller input and probes it with the larger,
and is the usual choice for large unsorted equality joins. A sort-merge join
sorts both inputs and walks them in parallel, which pays off when the inputs are
already sorted or the join is on a range.
