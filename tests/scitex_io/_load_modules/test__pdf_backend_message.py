#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The no-backend ImportError must name a package that actually helps.

NO MOCKS: asserts on the module-level ``NO_PDF_BACKEND_MESSAGE`` constant
rather than forcing the raise. Reaching that branch means all three backends
absent, which would mean faking three import flags -- and this package does
not test with mocks. The constant IS the message the raise uses, so pinning it
pins the behaviour.

ONE assertion per test, AAA-structured.
"""

from scitex_io._load_modules._pdf_utils import NO_PDF_BACKEND_MESSAGE


def test_message_names_pypdf_the_module_actually_imported():
    # Arrange -- _pdf_utils imports `pypdf`; the old text said `PyPDF2`.
    # Act
    text = NO_PDF_BACKEND_MESSAGE
    # Assert
    assert "pip install pypdf" in text


def test_message_warns_that_pypdf2_will_not_work():
    # Arrange -- a reader who already ran `pip install PyPDF2` on the old
    # advice needs to be told WHY it changed nothing, not just given a new
    # command. The renamed-package fact is the part that unsticks them.
    # Act
    text = NO_PDF_BACKEND_MESSAGE
    # Assert
    assert "will NOT satisfy this import" in text


def test_message_does_not_tell_anyone_to_install_pypdf2():
    # Arrange -- regression guard. This exact instruction cost a full
    # investigation: it is followed, it does nothing, and the reader ends up
    # back at the identical error with the message's credibility spent.
    # Act
    lines = NO_PDF_BACKEND_MESSAGE.splitlines()
    # Assert
    assert not any(line.strip().startswith("pip install PyPDF2") for line in lines)


def test_message_flags_pymupdf_as_agpl():
    # Arrange -- PyMuPDF was previously labelled "# Recommended" with no
    # licence note, so the option pushed hardest was the only copyleft one.
    # Act
    text = NO_PDF_BACKEND_MESSAGE
    # Assert
    assert "AGPL-3.0" in text


def test_message_no_longer_recommends_a_backend_without_saying_why():
    # Arrange -- ranking is fine, silent ranking is not. The bare
    # "# Recommended" tag is gone; each option now carries its licence.
    # Act
    text = NO_PDF_BACKEND_MESSAGE
    # Assert
    assert "# Recommended" not in text
