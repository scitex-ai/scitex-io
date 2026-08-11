"""The no-backend ImportError must name a remedy that actually works.

This message is the first — and usually only — thing that tells a consumer
`load(path, mode="text")` needs a backend installed at all. It is therefore
load-bearing documentation, not decoration, and it earned tests the hard
way: it previously said `pip install PyPDF2` while this module imports the
module `pypdf`, so a reader who followed the instruction installed a
package that did not resolve the error and arrived back at the same
failure.

Asserting on the constant rather than forcing the raise: reaching the
"no backend available" branch would mean faking three module-level import
flags, and this package does not test with mocks.
"""

from __future__ import annotations

from scitex_io._load_modules import _pdf_utils


def test_message_names_the_default_permissive_extra():
    # Arrange
    module = _pdf_utils
    # Act
    message = module.NO_PDF_BACKEND_MESSAGE
    # Assert -- the extra a consumer should reach for first.
    assert '"scitex-io[pdf]"' in message


def test_message_names_the_table_extra():
    # Arrange
    module = _pdf_utils
    # Act
    message = module.NO_PDF_BACKEND_MESSAGE
    # Assert
    assert '"scitex-io[pdf-tables]"' in message


def test_message_names_the_fast_extra():
    # Arrange
    module = _pdf_utils
    # Act
    message = module.NO_PDF_BACKEND_MESSAGE
    # Assert
    assert '"scitex-io[pdf-fast]"' in message


def test_message_does_not_tell_the_reader_to_install_pypdf2():
    """The regression this file exists for.

    `_pdf_utils` imports `pypdf`, never `PyPDF2`. Naming PyPDF2 sends the
    reader to install a package that leaves the ImportError exactly where
    it was. Matching case-sensitively on the distribution name so the
    substring `pypdf` (which IS correct, and appears in the message) does
    not trip this.
    """
    # Arrange
    module = _pdf_utils
    # Act
    message = module.NO_PDF_BACKEND_MESSAGE
    # Assert
    assert "PyPDF2" not in message


def test_message_flags_the_agpl_licence_on_the_fast_backend():
    """PyMuPDF is AGPL-3.0 absent a commercial licence.

    A consumer choosing a backend from this message is making a licensing
    decision whether or not they realise it, so the message says so at the
    point of choice rather than leaving it to be discovered in a dependency
    audit later.
    """
    # Arrange
    module = _pdf_utils
    # Act
    message = module.NO_PDF_BACKEND_MESSAGE
    # Assert
    assert "AGPL-3.0" in message


# ---------------------------------------------------------------------------
# The DEGRADED paths — a backend exists, but not the preferred one.
#
# These are the sites scitex-dev's 2026-08-11 ruling actually turns on. The
# no-backend message above was already correct; these two still said
# "pip install PyMuPDF" with no mention of the extra and no mention of the
# licence. That is the silent-AGPL-acquisition surface the carve-out exists to
# prevent, reachable by anyone who installed [all] and asked for a mode that
# prefers fitz.
#
# The ruling's condition for the carve-out being honest rather than a hole:
# the exclusion must be VISIBLE AT THE POINT OF FAILURE, naming the extra AND
# the licence. These tests are that condition, asserted.
# ---------------------------------------------------------------------------
def test_fast_fallback_names_the_extra_not_the_bare_package():
    # Arrange
    module = _pdf_utils
    # Act
    message = module.MISSING_FAST_BACKEND_MESSAGE
    # Assert
    assert '"scitex-io[pdf-fast]"' in message


def test_fast_fallback_states_the_agpl_licence():
    # Arrange
    module = _pdf_utils
    # Act
    message = module.MISSING_FAST_BACKEND_MESSAGE
    # Assert
    assert "AGPL-3.0" in message


def test_fast_fallback_says_why_all_does_not_include_it():
    """A silent omission from [all] is an under-install; a stated one is a choice.

    Without this sentence the reader knows only that something is missing --
    not that it was withheld deliberately, nor why -- and the obvious repair
    is to acquire the copyleft dependency without registering that they did.
    """
    # Arrange
    module = _pdf_utils
    # Act
    message = module.MISSING_FAST_BACKEND_MESSAGE
    # Assert
    assert "scitex-io[all]" in message


def test_tables_fallback_names_the_extra_not_the_bare_package():
    # Arrange
    module = _pdf_utils
    # Act
    message = module.MISSING_TABLES_BACKEND_MESSAGE
    # Assert
    assert '"scitex-io[pdf-tables]"' in message


def test_no_degraded_message_tells_the_reader_to_install_pypdf2():
    """Same regression guard as above, applied to the paths it was missing from.

    The original defect was only ever fixed in the no-backend message. A
    remedy string that names a package which cannot resolve the problem does
    not merely fail to help -- it OVERWRITES correct knowledge in the reader,
    including a reader who had already measured the truth. Guarding every
    site, not the one that was noticed first.
    """
    # Arrange
    module = _pdf_utils
    # Act
    both = module.MISSING_FAST_BACKEND_MESSAGE + module.MISSING_TABLES_BACKEND_MESSAGE
    # Assert
    assert "PyPDF2" not in both
