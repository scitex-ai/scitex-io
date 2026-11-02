# Native release qualification

The tag workflow resolves an existing release tag against protected main before
using the central registered leaf executor for the complete test and artifact
build operations. Native execution verifies the immutable whole image and
runtime, then creates an exclusive temporary context. The test driver performs
one normal `.[all,dev]` installation and dependency check in a fresh environment
inside that image. It does not fall back to a smaller dependency set.

All caches, package state, plotting configuration and temporary outputs belong
to that context. The shared lifecycle checks its device, inode, owner and child
group before cleanup; a replacement directory is retained and reported.

The hosted publisher validates both complete artifacts against source bytes and
generated metadata before requesting an OIDC token. Revalidation includes the
release tag and promoted source commit. The GitHub release receives the same
verified wheel and source distribution.

This migration is not yet registered for publication. The IO native profile,
its complete helper closure and actual immutable-image execution must qualify
before its central registration and final caller pin are approved. No tag or
publication is performed by adding these source files.


### Owned cleanup resource policy

The normal complete `.[all,dev]` environment measured 113,918 regular files
and about 16.0 GB as the sum of allocated blocks per entry on the E846 image. The former ten-second deletion
budget returned status 124 with the exact root identity unchanged; tests had
passed. This is a filesystem cleanup limit, separate from product, kernel and
test subprocess deadlines.

IO now surveys **all entries, including directories**, and allocated blocks per entry (hardlinks count per entry)
without following links or crossing filesystems, with a ten-second survey bound.
Reviewed roots with at most 10,000 entries and 1 GiB keep a ten-second removal
budget. Roots with at most 200,000 entries and 32 GiB receive sixty seconds.
Unknown or larger roots are retained and fail the job; there is no automatic
extension beyond this profile. The inode, UID, mode, symlink, process-birth,
child-group and one-filesystem guards remain, and root identity is checked again
after the survey. Both survey/removal failure evidence survives outer cleanup.


### Lazy import and first-event provenance

A bare `import scitex_io` loads neither distribution metadata nor observer
providers. `__version__` still returns the installed distribution's string,
resolved on first access. Automatic observer discovery completes before first
public IO API access or internal event dispatch. Neutral `register_post_*`
functions append callbacks without starting discovery; explicit callbacks keep
actual registration order. Automatic providers therefore follow the deferred
activation point rather than import-time ordering relative to earlier manual
registrations.

Activation state is protected by a condition, while actual provider imports
and registrar calls run outside that lock. Other IO callers wait for first
activation; provider imports can register callbacks without deadlocking.
Actual installed consumer-wheel regressions cover first save/load, ordering,
concurrent first operations and both Clew/IO import orders.

The native driver wraps the complete suite in an owned PostgreSQL context and
also requires a first-save citation-ledger proof through
`scitex_dev.store.testing.ephemeral_cluster_dsn()`: a new private PostgreSQL
cluster and Unix socket, with configured PG variables cleared and an owned
empty password file. A fresh child imports IO first, saves a synthetic citation
artifact, then verifies its row through Clew's public API. Internet socket
creation is denied at the kernel syscall boundary; Python socket connects are
restricted to the private socket, and native libpq receives only the validated
private Unix-socket DSN. This is a controlled fixture, not a general sandbox
for arbitrary untrusted code. Failure to enforce the offline boundary fails
qualification. The installed-wheel smoke also runs in an owned private cluster. Earlier
installer/import phases have an explicit unavailable private Unix-socket DSN,
never an unset DSN. No host or fleet store is used, and teardown is verified.


### Admitted worker budget

The IO release profile declares a hard maximum of four pytest workers per
runner service through `CI_XDIST_WORKERS`; the executor validates and explicitly
passes it through the clean container environment. The actual worker count is
clamped by CPU affinity and any visible cgroup CPU quota. An absent or invalid
budget fails; the profile does not automatically consume every node CPU.

This is bounded workload admission, not an exclusive CPU guarantee. The review
observed 32 CPUs and eight eligible online services on compute-04; compute-03
has 32 CPUs, one eligible native service, and a separate Docker runner without
the required org-CPU label. No runner configuration was changed. Qualification
uses the same declared budget of four, while ordinary repository CI retains its
own caller configuration. Test selection, coverage and operation deadlines stay
unchanged.
