# Database Transactions and ACID

<!-- category: databases -->

## ACID
A transaction groups several statements into a single unit that is Atomic,
Consistent, Isolated, and Durable. Either all of its statements take effect on
COMMIT, or none do after a ROLLBACK.

## Isolation levels
Isolation levels trade consistency for concurrency. READ COMMITTED prevents dirty
reads, REPEATABLE READ also prevents non-repeatable reads, and SERIALIZABLE is the
strictest, behaving as if transactions ran one at a time.

## Deadlocks
A deadlock occurs when two transactions each hold a lock the other needs. The
database detects the cycle and aborts one transaction so the other can proceed; the
aborted transaction should be retried.
