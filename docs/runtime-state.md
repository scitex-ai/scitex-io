# Runtime state

`.scitex/io/runtime/` holds regenerable caches, logs, and per-run outputs for
scitex-io. The repository's [Git ignore policy](../.gitignore) excludes package
runtime state. No file beneath `runtime/` is tracked, including its local ignore
file. An existing local runtime directory uses a `.gitignore` containing `*`
with no exceptions, as checked by scitex-dev's PS-234 rule.

Configuration and source remain outside that directory. Removing the old
runtime placeholders from the Git index retains existing local files.
