#!/usr/bin/env python3
"""Real tests for scitex_io._save_modules._html.save_html."""

import pandas as pd
import pytest

from scitex_io._save_modules._html import save_html


def test_save_dataframe_via_to_html(tmp_path):
    """Save DataFrame using its write_html-equivalent via raw HTML string."""
    # Arrange
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    html_str = df.to_html()
    p = str(tmp_path / "df.html")
    save_html(html_str, p)
    back = pd.read_html(p)[0]
    # to_html includes an unnamed index column; drop it
    # Act
    if back.columns[0] == "Unnamed: 0":
        back = back.drop(columns=[back.columns[0]])
    # Assert
    assert list(back["a"]) == [1, 2]


def test_save_plotly_figure(tmp_path):
    """Plotly Figure exposes .write_html() — use the first branch."""
    # Arrange
    import plotly.graph_objects as go

    fig = go.Figure(go.Scatter(x=[1, 2], y=[3, 4]))
    p = str(tmp_path / "plot.html")
    save_html(fig, p)
    # Act
    text = open(p).read()
    # Assert
    assert "<html" in text.lower() or "plotly" in text.lower()


def test_save_html_string(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "raw.html")
    # Act
    # Act
    save_html("<html><body>hi</body></html>", p)
    # Assert
    # Assert
    assert "hi" in open(p).read()


def test_save_other_via_plotly_io(tmp_path):
    """Non-plotly, non-str → falls through to plotly.io.write_html which raises."""
    # Arrange
    # Act
    p = str(tmp_path / "fail.html")
    # Plotly will reject a list — that exercises the else branch
    # Assert
    with pytest.raises(Exception):
        save_html([1, 2, 3], p)
