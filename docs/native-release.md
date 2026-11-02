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
and about 16.0 GB allocated on the E846 image. The former ten-second deletion
budget returned status 124 with the exact root identity unchanged; tests had
passed. This is a filesystem cleanup limit, separate from product, kernel and
test subprocess deadlines.

IO now surveys **all entries, including directories**, and allocated blocks
without following links or crossing filesystems, with a ten-second survey bound.
Reviewed roots with at most 10,000 entries and 1 GiB keep a ten-second removal
budget. Roots with at most 200,000 entries and 32 GiB receive sixty seconds.
Unknown or larger roots are retained and fail the job; there is no automatic
extension beyond this profile. The inode, UID, mode, symlink, process-birth,
child-group and one-filesystem guards remain, and root identity is checked again
after the survey. Both survey/removal failure evidence survives outer cleanup.
