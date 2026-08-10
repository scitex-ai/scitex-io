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
