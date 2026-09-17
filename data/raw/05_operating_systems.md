# Operating Systems — Study Notes

## Processes and Threads

A process is a program in execution with its own address space, file descriptors
and other resources. A thread is a unit of execution inside a process; threads of
the same process share the address space and open files but each has its own
stack, registers and program counter.

The consequence of sharing is that inter-thread communication is cheap — they
simply read the same memory — while inter-process communication needs an explicit
mechanism such as pipes, message queues, shared memory segments or sockets. The
other consequence is that threads can corrupt each other's data, which is why
synchronisation primitives exist.

Context switching between threads of one process is cheaper than switching
between processes, because the memory mapping and therefore the translation
lookaside buffer does not need to be replaced.

## Scheduling

The scheduler decides which ready process runs next. First-come first-served is
simple but suffers the convoy effect, where one long job delays every short job
behind it. Shortest job first minimises average waiting time but requires knowing
run times in advance and can starve long jobs. Round robin gives each process a
fixed time quantum and is the basis of interactive scheduling; a quantum that is
too short wastes time on context switches, while one that is too long degrades
into first-come first-served. Priority scheduling can starve low-priority
processes, which ageing fixes by gradually raising the priority of waiting jobs.

Preemptive scheduling can interrupt a running process; cooperative scheduling
waits for it to yield, which means one misbehaving process can freeze the system.

## Synchronisation

A race condition occurs when the result depends on the unpredictable interleaving
of concurrent operations on shared state. The critical section is the code region
that touches that shared state, and it must be executed by only one thread at a
time.

A mutex provides mutual exclusion with lock and unlock, and has an owner — only
the locking thread may unlock it. A semaphore is a counter with wait and signal
operations; a counting semaphore permits up to N concurrent holders, and has no
ownership, so it can be signalled by a different thread than the one that waited.
A condition variable lets a thread sleep until another thread signals that some
predicate became true, and is always used together with a mutex.

Deadlock requires four conditions to hold simultaneously: mutual exclusion, hold
and wait, no preemption, and circular wait. Breaking any one of them prevents
deadlock. The most common practical technique is to impose a global lock ordering
so that circular wait cannot occur.

Starvation is different from deadlock: no thread is blocked forever by a cycle,
but one particular thread never gets scheduled or never acquires the resource.

## Memory Management

Virtual memory gives each process the illusion of a large private address space.
The memory management unit translates virtual addresses to physical ones using
page tables, and the translation lookaside buffer caches recent translations so
most translations avoid a page table walk.

A page fault occurs when a referenced page is not resident in physical memory;
the OS suspends the process, loads the page from disk, and resumes it. Thrashing
is the pathological state where processes spend more time servicing page faults
than executing, caused by over-committing memory.

Page replacement algorithms decide which page to evict. FIFO is simple but can
suffer Belady's anomaly, where adding more frames increases the fault rate. LRU
evicts the least recently used page and approximates optimal behaviour well,
though exact LRU is expensive, so real systems use clock or second-chance
approximations. The optimal algorithm evicts the page used furthest in the
future, and is unimplementable but useful as a benchmark.

Internal fragmentation is wasted space inside an allocated block, caused by
rounding an allocation up to a fixed page or block size. External fragmentation
is free memory split into pieces too small to satisfy a request, and paging
largely eliminates it because any free frame can back any virtual page.

## File Systems

A file system maps file names to blocks on a storage device. An inode holds a
file's metadata — size, permissions, timestamps and block pointers — but not its
name; the name lives in a directory entry that points at the inode. This
separation is what allows hard links, where several directory entries reference
one inode.

Journalling records intended changes in a log before applying them, so an
interrupted write can be replayed or rolled back after a crash rather than
leaving the file system in an inconsistent state.
