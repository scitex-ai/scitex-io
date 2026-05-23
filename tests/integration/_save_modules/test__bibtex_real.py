"""Real round-trip tests for scitex_io bibtex save+load."""


from __future__ import annotations
from scitex_io._load_modules._bibtex import (
    _load_bibtex,
    _parse_bibtex_content,
    _parse_bibtex_fields,
    _parse_bibtex_fields_basic,
    _unescape_bibtex,
    load_bibtex,
)
from scitex_io._save_modules._bibtex import (
    _entry_to_bibtex,
    _escape_bibtex,
    save_bibtex,
)


# -----------------------------
# _escape_bibtex / _unescape_bibtex
# -----------------------------
def test_escape_bibtex_special_chars_escape_bibtex_a_b_a_b():
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert _escape_bibtex("a & b") == r"a \& b"


def test_escape_bibtex_special_chars_escape_bibtex_50_50():
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert _escape_bibtex("50%") == r"50\%"


def test_escape_bibtex_special_chars_escape_bibtex_x_x():
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert _escape_bibtex("$x$") == r"\$x\$"


def test_escape_bibtex_special_chars_escape_bibtex_a_b_c_a_b_c():
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert _escape_bibtex("a#b_c") == r"a\#b\_c"




def test_unescape_bibtex_round_trip_for_simple_chars():
    # Arrange
    # Act
    # Arrange
    # Act
    out = _unescape_bibtex(r"a \& b \% c \$ \# \_")
    # Assert
    # Assert
    assert "&" in out and "%" in out and "$" in out and "#" in out and "_" in out


# -----------------------------
# _entry_to_bibtex
# -----------------------------
def test_entry_to_bibtex_basic_out_startswith_article_doe2020():
    # Arrange
    # Arrange
    entry = {
        "entry_type": "article",
        "key": "doe2020",
        "fields": {"title": "Hello", "year": "2020", "author": "Doe, J."},
    }
    # Act
    out = _entry_to_bibtex(entry)
    # Act
    # Assert
    # Assert
    assert out.startswith("@article{doe2020,")


def test_entry_to_bibtex_basic_title_hello_in_out():
    # Arrange
    # Arrange
    entry = {
        "entry_type": "article",
        "key": "doe2020",
        "fields": {"title": "Hello", "year": "2020", "author": "Doe, J."},
    }
    # Act
    out = _entry_to_bibtex(entry)
    # Act
    # Assert
    # Assert
    assert "title = {Hello}" in out


def test_entry_to_bibtex_basic_out_rstrip_endswith():
    # Arrange
    # Arrange
    entry = {
        "entry_type": "article",
        "key": "doe2020",
        "fields": {"title": "Hello", "year": "2020", "author": "Doe, J."},
    }
    # Act
    out = _entry_to_bibtex(entry)
    # Act
    # Assert
    # Assert
    assert out.rstrip().endswith("}")




def test_entry_to_bibtex_default_type_and_key():
    # Arrange
    # Act
    # Arrange
    # Act
    out = _entry_to_bibtex({"fields": {"a": "1"}})
    # Assert
    # Assert
    assert out.startswith("@misc{unknown,")


def test_entry_to_bibtex_escapes_special_chars():
    # Arrange
    # Arrange
    e = {
        "entry_type": "misc",
        "key": "k",
        "fields": {"title": "Lions & Tigers $50%"},
    }
    # Act
    # Act
    out = _entry_to_bibtex(e)
    # Assert
    # Assert
    assert r"\&" in out and r"\%" in out and r"\$" in out


# -----------------------------
# save_bibtex
# -----------------------------
def test_save_bibtex_single_entry_round_trip_len_entries_is_1(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "a.bib")
    entry = {
        "entry_type": "article",
        "key": "smith2021",
        "fields": {"title": "A Study", "year": "2021", "author": "Smith"},
    }
    save_bibtex(entry, p)
    # Act
    entries = _load_bibtex(p)
    # Act
    # Assert
    # Assert
    assert len(entries) == 1


def test_save_bibtex_single_entry_round_trip_entries_0_entry_type_article(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "a.bib")
    entry = {
        "entry_type": "article",
        "key": "smith2021",
        "fields": {"title": "A Study", "year": "2021", "author": "Smith"},
    }
    save_bibtex(entry, p)
    # Act
    entries = _load_bibtex(p)
    # Act
    # Assert
    # Assert
    assert entries[0]["entry_type"] == "article"


def test_save_bibtex_single_entry_round_trip_entries_0_key_smith2021(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "a.bib")
    entry = {
        "entry_type": "article",
        "key": "smith2021",
        "fields": {"title": "A Study", "year": "2021", "author": "Smith"},
    }
    save_bibtex(entry, p)
    # Act
    entries = _load_bibtex(p)
    # Act
    # Assert
    # Assert
    assert entries[0]["key"] == "smith2021"


def test_save_bibtex_single_entry_round_trip_entries_0_fields_title_a_study(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "a.bib")
    entry = {
        "entry_type": "article",
        "key": "smith2021",
        "fields": {"title": "A Study", "year": "2021", "author": "Smith"},
    }
    save_bibtex(entry, p)
    # Act
    entries = _load_bibtex(p)
    # Act
    # Assert
    # Assert
    assert entries[0]["fields"]["title"] == "A Study"


def test_save_bibtex_single_entry_round_trip_entries_0_fields_year_2021(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "a.bib")
    entry = {
        "entry_type": "article",
        "key": "smith2021",
        "fields": {"title": "A Study", "year": "2021", "author": "Smith"},
    }
    save_bibtex(entry, p)
    # Act
    entries = _load_bibtex(p)
    # Act
    # Assert
    # Assert
    assert entries[0]["fields"]["year"] == "2021"




def test_save_bibtex_list_of_entries_len_entries_out_is_2(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "b.bib")
    entries_in = [
        {"entry_type": "article", "key": "a1", "fields": {"title": "T1"}},
        {"entry_type": "book", "key": "b1", "fields": {"title": "T2"}},
    ]
    save_bibtex(entries_in, p)
    # Act
    entries_out = _load_bibtex(p)
    # Act
    # Assert
    # Assert
    assert len(entries_out) == 2


def test_save_bibtex_list_of_entries_a1_in_keys_and_b1_in_keys(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "b.bib")
    entries_in = [
        {"entry_type": "article", "key": "a1", "fields": {"title": "T1"}},
        {"entry_type": "book", "key": "b1", "fields": {"title": "T2"}},
    ]
    save_bibtex(entries_in, p)
    # Act
    entries_out = _load_bibtex(p)
    # Assert
    assert len(entries_out) == 2
    keys = [e["key"] for e in entries_out]
    # Act
    # Assert
    assert "a1" in keys and "b1" in keys




def test_save_bibtex_no_header(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "c.bib")
    save_bibtex(
        {"entry_type": "misc", "key": "k", "fields": {"title": "X"}},
        p,
        add_header=False,
    )
    # Act
    # Act
    with open(p) as f:
        text = f.read()
    # Assert
    # Assert
    assert not text.lstrip().startswith("%")


def test_save_bibtex_append_mode(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "d.bib")
    save_bibtex({"entry_type": "misc", "key": "k1", "fields": {"t": "x"}}, p)
    save_bibtex(
        {"entry_type": "misc", "key": "k2", "fields": {"t": "y"}},
        p,
        append=True,
    )
    entries = _load_bibtex(p)
    # Act
    # Act
    keys = [e["key"] for e in entries]
    # Assert
    # Assert
    assert "k1" in keys and "k2" in keys


# -----------------------------
# _load_bibtex / parse helpers
# -----------------------------
def test_load_bibtex_basic_mode_len_entries_is_1(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "e.bib"
    p.write_text("@article{x1,\n  title = {Hello},\n  year = {2020}\n}\n")
    # Act
    entries = _load_bibtex(str(p), parse_mode="basic")
    # Act
    # Assert
    # Assert
    assert len(entries) == 1


def test_load_bibtex_basic_mode_entries_0_fields_title_hello(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "e.bib"
    p.write_text("@article{x1,\n  title = {Hello},\n  year = {2020}\n}\n")
    # Act
    entries = _load_bibtex(str(p), parse_mode="basic")
    # Act
    # Assert
    # Assert
    assert entries[0]["fields"]["title"] == "Hello"


def test_load_bibtex_basic_mode_entries_0_fields_year_2020(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "e.bib"
    p.write_text("@article{x1,\n  title = {Hello},\n  year = {2020}\n}\n")
    # Act
    entries = _load_bibtex(str(p), parse_mode="basic")
    # Act
    # Assert
    # Assert
    assert entries[0]["fields"]["year"] == "2020"




def test_load_bibtex_quoted_value():
    # Arrange
    # Arrange
    content = '@misc{k,\n  title = "Quoted Value",\n  year = "1999"\n}\n'
    # Act
    # Act
    entries = _parse_bibtex_content(content, "full")
    # Assert
    # Assert
    assert entries[0]["fields"]["title"] == "Quoted Value"


def test_load_bibtex_full_uppercase_type():
    # Arrange
    # Arrange
    content = "@ARTICLE{k,\n  title = {Up},\n  year = {2000}\n}\n"
    # Act
    # Act
    entries = _parse_bibtex_content(content, "full")
    # Assert
    # Assert
    assert entries[0]["entry_type"] == "article"


def test_load_bibtex_missing_file_raises(tmp_path):
    # Arrange
    # Arrange
    import pytest

    # Act
    # Act
    p = tmp_path / "missing.bib"
    # Assert
    # Assert
    with pytest.raises(ValueError):
        _load_bibtex(str(p))


def test_load_bibtex_convenience_alias(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "f.bib"
    p.write_text("@misc{k,\n  title = {T}\n}\n")
    # Act
    # Act
    out = load_bibtex(str(p))
    # Assert
    # Assert
    assert out[0]["key"] == "k"


def test_parse_fields_basic_handles_quoted_and_braced_fields_title_hello():
    # Arrange
    # Arrange
    # Act
    fields = _parse_bibtex_fields_basic('  title = {Hello},\n  year = "2020"\n')
    # Act
    # Assert
    # Assert
    assert fields["title"] == "Hello"


def test_parse_fields_basic_handles_quoted_and_braced_fields_year_2020():
    # Arrange
    # Arrange
    # Act
    fields = _parse_bibtex_fields_basic('  title = {Hello},\n  year = "2020"\n')
    # Act
    # Assert
    # Assert
    assert fields["year"] == "2020"




def test_parse_fields_full_unescapes_special_chars():
    # Arrange
    # Arrange
    body = "  title = {a \\& b}\n"
    # Act
    # Act
    fields = _parse_bibtex_fields(body)
    # Assert
    # Assert
    assert "&" in fields["title"]


# -----------------------------
# Paper / PaperCollection passthrough
# -----------------------------
class _FakePaper:
    """Mimic scitex.scholar.Paper enough to exercise the save passthrough."""

    def _to_bibtex(self, include_enriched=True):
        return "@article{x, title={T}}"


class _FakePaperCollection:
    def __init__(self):
        self._papers = [_FakePaper(), _FakePaper()]

    def _to_bibtex(self, include_enriched=True):
        return "@article{a, title={A}}\n@article{b, title={B}}\n"


def test_save_bibtex_paper_passthrough_article_in_text_and_t_in_text(tmp_path):
    # Arrange
    # Arrange
    p = _FakePaper()
    # Force class name match.
    p.__class__.__name__ = "Paper"
    out = tmp_path / "p.bib"
    save_bibtex(p, str(out))
    # Act
    text = out.read_text()
    # Act
    # Assert
    # Assert
    assert "@article" in text and "T" in text


def test_save_bibtex_paper_passthrough_bibtex_entry_in_text(tmp_path):
    # Arrange
    # Arrange
    p = _FakePaper()
    # Force class name match.
    p.__class__.__name__ = "Paper"
    out = tmp_path / "p.bib"
    save_bibtex(p, str(out))
    # Act
    text = out.read_text()
    # Act
    # Assert
    # Assert
    assert "BibTeX entry" in text




def test_save_bibtex_paper_collection_passthrough_article_a_in_text_and_article_b_in_text(tmp_path):
    # Arrange
    # Arrange
    coll = _FakePaperCollection()
    coll.__class__.__name__ = "PaperCollection"
    out = tmp_path / "pc.bib"
    save_bibtex(coll, str(out))
    # Act
    text = out.read_text()
    # Act
    # Assert
    # Assert
    assert "@article{a" in text and "@article{b" in text


def test_save_bibtex_paper_collection_passthrough_bibtex_bibliography_in_text(tmp_path):
    # Arrange
    # Arrange
    coll = _FakePaperCollection()
    coll.__class__.__name__ = "PaperCollection"
    out = tmp_path / "pc.bib"
    save_bibtex(coll, str(out))
    # Act
    text = out.read_text()
    # Act
    # Assert
    # Assert
    assert "BibTeX bibliography" in text


