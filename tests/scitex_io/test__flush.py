#!/usr/bin/env python3
# Timestamp: "2025-05-31"
# File: test__flush.py

"""Tests for the flush function in scitex.io module."""

import io
import os
import sys
from unittest.mock import Mock, patch

import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")


class TestFlushBasic:
    """Test basic flush functionality."""

    def test_flush_normal_operation(self):
        """Test flush in normal operation."""
        # Arrange
        # Act
        # Assert
        from scitex_io import flush

        # Create mock objects
        mock_stdout = Mock()
        mock_stderr = Mock()
        mock_sys = Mock()
        mock_sys.stdout = mock_stdout
        mock_sys.stderr = mock_stderr

        with patch("os.sync") as mock_sync:
            # Call flush with mock sys
            flush(sys=mock_sys)

            # Verify all flush operations were called
            mock_stdout.flush.assert_called_once()
            mock_stderr.flush.assert_called_once()
            mock_sync.assert_called_once()

    def test_flush_default_sys(self):
        """Test flush with default sys parameter."""
        # Arrange
        # Act
        # Assert
        from scitex_io import flush

        # Mock the actual sys module's stdout and stderr
        with (
            patch("sys.stdout.flush") as mock_stdout_flush,
            patch("sys.stderr.flush") as mock_stderr_flush,
            patch("os.sync") as mock_sync,
        ):
            # Call flush without parameters (uses default sys)
            flush()

            # Verify operations were called
            mock_stdout_flush.assert_called_once()
            mock_stderr_flush.assert_called_once()
            mock_sync.assert_called_once()

    def test_flush_with_none_sys(self):
        """Test flush behavior when sys is None."""
        # Arrange
        # Act
        # Assert
        from scitex_io import flush

        with patch("os.sync") as mock_sync:
            with pytest.warns(UserWarning, match="flush needs sys"):
                flush(sys=None)
            mock_sync.assert_not_called()


class TestFlushErrorHandling:
    """Test error handling in flush function."""

    def test_flush_stdout_error(self):
        """Test flush when stdout.flush() raises an error."""
        # Arrange
        # Act
        # Assert
        from scitex_io import flush

        # Create mock sys with failing stdout
        mock_sys = Mock()
        mock_sys.stdout.flush.side_effect = OSError("stdout flush failed")
        mock_sys.stderr = Mock()

        with patch("os.sync"):
            # Should raise the error
            with pytest.raises(IOError, match="stdout flush failed"):
                flush(sys=mock_sys)

    def test_flush_stderr_error(self):
        """Test flush when stderr.flush() raises an error."""
        # Arrange
        # Act
        # Assert
        from scitex_io import flush

        # Create mock sys with failing stderr
        mock_sys = Mock()
        mock_sys.stdout = Mock()
        mock_sys.stderr.flush.side_effect = OSError("stderr flush failed")

        with patch("os.sync"):
            # Should raise the error
            with pytest.raises(IOError, match="stderr flush failed"):
                flush(sys=mock_sys)

    def test_flush_sync_error(self):
        """Test flush when os.sync() raises an error."""
        # Arrange
        # Act
        # Assert
        from scitex_io import flush

        mock_sys = Mock()
        mock_sys.stdout = Mock()
        mock_sys.stderr = Mock()

        with patch("os.sync", side_effect=OSError("sync failed")):
            # Should raise the error
            with pytest.raises(OSError, match="sync failed"):
                flush(sys=mock_sys)


class TestFlushWithRealIO:
    """Test flush with real IO operations."""

    def test_flush_with_buffered_output(self, capsys):
        """Test flush actually flushes buffered output."""
        # Arrange
        from scitex_io import flush

        # Write to stdout without newline (usually buffered)
        sys.stdout.write("test output")

        # Flush should make it appear
        with patch("os.sync"):  # Don't actually sync filesystem
            flush()

        # Check output appeared
        # Act
        captured = capsys.readouterr()
        # Assert
        assert "test output" in captured.out

    def test_flush_with_string_io_stdout_io_getvalue_stdout_data(self):
        # Arrange
        # Arrange
        from scitex_io import flush
        # Create StringIO objects
        stdout_io = io.StringIO()
        stderr_io = io.StringIO()
        # Create mock sys with StringIO
        mock_sys = Mock()
        mock_sys.stdout = stdout_io
        mock_sys.stderr = stderr_io
        # Write some data
        stdout_io.write("stdout data")
        stderr_io.write("stderr data")
        # Act
        with patch("os.sync"):
            # Flush should work with StringIO
            flush(sys=mock_sys)
        # Act
        # Assert
        # Assert
        assert stdout_io.getvalue() == "stdout data"

    def test_flush_with_string_io_stderr_io_getvalue_stderr_data(self):
        # Arrange
        # Arrange
        from scitex_io import flush
        # Create StringIO objects
        stdout_io = io.StringIO()
        stderr_io = io.StringIO()
        # Create mock sys with StringIO
        mock_sys = Mock()
        mock_sys.stdout = stdout_io
        mock_sys.stderr = stderr_io
        # Write some data
        stdout_io.write("stdout data")
        stderr_io.write("stderr data")
        # Act
        with patch("os.sync"):
            # Flush should work with StringIO
            flush(sys=mock_sys)
        # Act
        # Assert
        # Assert
        assert stderr_io.getvalue() == "stderr data"



class TestFlushEdgeCases:
    """Test edge cases for flush function."""

    def test_flush_closed_stdout(self):
        """Test flush with closed stdout."""
        # Arrange
        # Act
        # Assert
        from scitex_io import flush

        # Create mock sys with closed stdout
        mock_sys = Mock()
        mock_stdout = Mock()
        mock_stdout.closed = True
        mock_stdout.flush.side_effect = ValueError("I/O operation on closed file")
        mock_sys.stdout = mock_stdout
        mock_sys.stderr = Mock()

        with patch("os.sync"):
            # Should raise error from closed file
            with pytest.raises(ValueError, match="closed file"):
                flush(sys=mock_sys)

    def test_flush_missing_flush_method(self):
        """Test flush when stdout/stderr don't have flush method."""
        # Arrange
        # Act
        # Assert
        from scitex_io import flush

        # Create mock sys with object lacking flush
        mock_sys = Mock()
        mock_sys.stdout = Mock(spec=[])  # No flush method
        mock_sys.stderr = Mock()

        with patch("os.sync"):
            # Should raise AttributeError
            with pytest.raises(AttributeError):
                flush(sys=mock_sys)

    def test_flush_with_custom_sys_object_custom_sys_stdout_flushed(self):
        # Arrange
        # Arrange
        from scitex_io import flush
        # Create custom sys-like object
        class CustomSys:
            def __init__(self):
                self.stdout = Mock()
                self.stderr = Mock()
                self.stdout_flushed = False
                self.stderr_flushed = False
                # Setup flush methods
                self.stdout.flush = lambda: setattr(self, "stdout_flushed", True)
                self.stderr.flush = lambda: setattr(self, "stderr_flushed", True)
        custom_sys = CustomSys()
        # Act
        with patch("os.sync"):
            flush(sys=custom_sys)
        # Act
        # Assert
        # Assert
        assert custom_sys.stdout_flushed

    def test_flush_with_custom_sys_object_custom_sys_stderr_flushed(self):
        # Arrange
        # Arrange
        from scitex_io import flush
        # Create custom sys-like object
        class CustomSys:
            def __init__(self):
                self.stdout = Mock()
                self.stderr = Mock()
                self.stdout_flushed = False
                self.stderr_flushed = False
                # Setup flush methods
                self.stdout.flush = lambda: setattr(self, "stdout_flushed", True)
                self.stderr.flush = lambda: setattr(self, "stderr_flushed", True)
        custom_sys = CustomSys()
        # Act
        with patch("os.sync"):
            flush(sys=custom_sys)
        # Act
        # Assert
        # Assert
        assert custom_sys.stderr_flushed



class TestFlushIntegration:
    """Test flush integration with other parts of the system."""

    def test_flush_after_print_line_1_in_captured_out(self, capsys):
        # Arrange
        # Arrange
        from scitex_io import flush
        # Print some data
        print("Line 1", end="")  # No newline, might be buffered
        print("Line 2", file=sys.stderr, end="")  # To stderr
        with patch("os.sync"):
            flush()
        # Check both outputs appeared
        # Act
        captured = capsys.readouterr()
        # Act
        # Assert
        # Assert
        assert "Line 1" in captured.out

    def test_flush_after_print_line_2_in_captured_err(self, capsys):
        # Arrange
        # Arrange
        from scitex_io import flush
        # Print some data
        print("Line 1", end="")  # No newline, might be buffered
        print("Line 2", file=sys.stderr, end="")  # To stderr
        with patch("os.sync"):
            flush()
        # Check both outputs appeared
        # Act
        captured = capsys.readouterr()
        # Act
        # Assert
        # Assert
        assert "Line 2" in captured.err


    def test_flush_multiple_times(self):
        """Test calling flush multiple times."""
        # Arrange
        # Act
        # Assert
        from scitex_io import flush

        mock_sys = Mock()
        mock_sys.stdout = Mock()
        mock_sys.stderr = Mock()

        with patch("os.sync") as mock_sync:
            # Call flush multiple times
            for _ in range(3):
                flush(sys=mock_sys)

            # Each flush should work independently
            assert mock_sys.stdout.flush.call_count == 3
            assert mock_sys.stderr.flush.call_count == 3
            assert mock_sync.call_count == 3

    def test_flush_thread_safety(self):
        """Test that flush can be called from multiple threads."""
        # Arrange
        import threading

        from scitex_io import flush

        mock_sys = Mock()
        mock_sys.stdout = Mock()
        mock_sys.stderr = Mock()

        errors = []

        def flush_in_thread():
            try:
                with patch("os.sync"):
                    flush(sys=mock_sys)
            except Exception as e:
                errors.append(e)

        # Create and start multiple threads
        threads = [threading.Thread(target=flush_in_thread) for _ in range(5)]
        for t in threads:
            t.start()
        # Act
        for t in threads:
            t.join()

        # No errors should occur
        # Assert
        assert len(errors) == 0


# --------------------------------------------------------------------------------

if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])

# --------------------------------------------------------------------------------
# Start of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_flush.py
# --------------------------------------------------------------------------------
# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# # Time-stamp: "2024-11-02 03:23:44 (ywatanabe)"
# # File: ./scitex_repo/src/scitex/io/_flush.py
#
# import os
# import sys
#
# from scitex import logging
#
# logger = logging.getLogger(__name__)
#
#
# def flush(sys=sys):
#     """
#     Flushes the system's stdout and stderr, and syncs the file system.
#     This ensures all pending write operations are completed.
#     """
#     if sys is None:
#         logger.warning("flush needs sys. Skipping.")
#     else:
#         sys.stdout.flush()
#         sys.stderr.flush()
#         os.sync()
#
#
# # EOF

# --------------------------------------------------------------------------------
# End of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_flush.py
# --------------------------------------------------------------------------------
