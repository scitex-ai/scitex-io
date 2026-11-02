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
