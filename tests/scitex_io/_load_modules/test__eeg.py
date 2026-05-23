#!/usr/bin/env python3
# Time-stamp: "2025-06-02 17:20:00 (ywatanabe)"
# File: ./scitex_repo/tests/scitex/io/_load_modules/test__eeg.py

"""Comprehensive tests for EEG neuroscience data loading functionality."""

import os
import tempfile

import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")
from unittest.mock import MagicMock, patch


class TestLoadEegAvailableFlags:
    """Test _AVAILABLE flags for optional dependencies."""

    def test_mne_available_flag_exists(self):
        """Test that MNE_AVAILABLE flag is exported."""
        # Arrange
        # Act
        from scitex_io._load_modules._eeg import MNE_AVAILABLE

        # Assert
        assert isinstance(MNE_AVAILABLE, bool)


class TestLoadEegData:
    """Test suite for _load_eeg_data function"""

    def test_valid_extension_check(self):
        """Test that function validates supported EEG extensions"""
        # Arrange
        # Act
        # Assert
        from scitex_io._load_modules._eeg import _load_eeg_data

        # Test invalid extensions
        invalid_files = ["file.txt", "data.wav", "signal.mat", "test.xlsx"]

        for invalid_file in invalid_files:
            with pytest.raises(
                ValueError, match="File must have one of these extensions"
            ):
                _load_eeg_data(invalid_file)

    def test_supported_extensions_list(self):
        """Test that all documented EEG extensions are supported"""
        # Arrange
        # Act
        # Assert
        from scitex_io._load_modules._eeg import _load_eeg_data

        # Test that function recognizes all supported formats
        supported_extensions = [
            "test.vhdr",
            "test.vmrk",
            "test.edf",
            "test.bdf",
            "test.gdf",
            "test.cnt",
            "test.egi",
            "test.eeg",
            "test.set",
        ]

        # These should not raise extension validation errors
        # (they'll fail later due to missing MNE data, but extension should be OK)
        for test_file in supported_extensions:
            with patch("scitex_io._load_modules._eeg.mne") as mock_mne:
                with patch(
                    "scitex_io._load_modules._eeg.os.path.isfile"
                ) as mock_isfile:
                    # For .eeg files, mock associated files exist
                    mock_isfile.return_value = True
                    mock_mne.io.read_raw_brainvision.side_effect = ValueError(
                        "test error"
                    )
                    mock_mne.io.read_raw_edf.side_effect = ValueError("test error")
                    mock_mne.io.read_raw_bdf.side_effect = ValueError("test error")
                    mock_mne.io.read_raw_gdf.side_effect = ValueError("test error")
                    mock_mne.io.read_raw_cnt.side_effect = ValueError("test error")
                    mock_mne.io.read_raw_egi.side_effect = ValueError("test error")
                    mock_mne.io.read_raw.side_effect = ValueError("test error")

                    # Should not raise extension error, but will raise MNE error
                    with pytest.raises(ValueError, match="test error"):
                        _load_eeg_data(test_file)

    @patch("scitex_io._load_modules._eeg.mne")
    @patch("scitex_io._load_modules._eeg.warnings")
    def test_brainvision_vhdr_loading(self, mock_warnings, mock_mne):
        """Test loading BrainVision .vhdr files"""
        # Arrange
        from scitex_io._load_modules._eeg import _load_eeg_data

        # Mock MNE raw object
        mock_raw = MagicMock()
        mock_mne.io.read_raw_brainvision.return_value = mock_raw

        # Call function
        result = _load_eeg_data("test_file.vhdr", verbose=False)

        # Verify MNE function was called correctly
        mock_mne.io.read_raw_brainvision.assert_called_once_with(
            "test_file.vhdr", preload=True, verbose=False
        )

        # Verify warnings were suppressed
        # Act
        mock_warnings.catch_warnings.assert_called_once()

        # Verify result
        # Assert
        assert result == mock_raw

    @patch("scitex_io._load_modules._eeg.mne")
    def test_brainvision_vmrk_loading(self, mock_mne):
        """Test loading BrainVision .vmrk files"""
        # Arrange
        from scitex_io._load_modules._eeg import _load_eeg_data

        mock_raw = MagicMock()
        mock_mne.io.read_raw_brainvision.return_value = mock_raw

        result = _load_eeg_data("markers.vmrk")

        # Act
        mock_mne.io.read_raw_brainvision.assert_called_once_with(
            "markers.vmrk", preload=True
        )
        # Assert
        assert result == mock_raw

    @patch("scitex_io._load_modules._eeg.mne")
    def test_edf_loading_result_equals_mock_raw(self, mock_mne):
        """Test loading European Data Format (.edf) files"""
        # Arrange
        from scitex_io._load_modules._eeg import _load_eeg_data

        mock_raw = MagicMock()
        mock_mne.io.read_raw_edf.return_value = mock_raw

        result = _load_eeg_data("eeg_data.edf", stim_channel="auto")

        # Act
        mock_mne.io.read_raw_edf.assert_called_once_with(
            "eeg_data.edf", preload=True, stim_channel="auto"
        )
        # Assert
        assert result == mock_raw

    @patch("scitex_io._load_modules._eeg.mne")
    def test_bdf_loading_result_equals_mock_raw(self, mock_mne):
        """Test loading BioSemi Data Format (.bdf) files"""
        # Arrange
        from scitex_io._load_modules._eeg import _load_eeg_data

        mock_raw = MagicMock()
        mock_mne.io.read_raw_bdf.return_value = mock_raw

        result = _load_eeg_data("biosemi_data.bdf", verbose=True)

        # Act
        mock_mne.io.read_raw_bdf.assert_called_once_with(
            "biosemi_data.bdf", preload=True, verbose=True
        )
        # Assert
        assert result == mock_raw

    @patch("scitex_io._load_modules._eeg.mne")
    def test_gdf_loading_result_equals_mock_raw(self, mock_mne):
        """Test loading General Data Format (.gdf) files"""
        # Arrange
        from scitex_io._load_modules._eeg import _load_eeg_data

        mock_raw = MagicMock()
        mock_mne.io.read_raw_gdf.return_value = mock_raw

        result = _load_eeg_data("general_data.gdf")

        # Act
        mock_mne.io.read_raw_gdf.assert_called_once_with(
            "general_data.gdf", preload=True
        )
        # Assert
        assert result == mock_raw

    @patch("scitex_io._load_modules._eeg.mne")
    def test_cnt_loading_result_equals_mock_raw(self, mock_mne):
        """Test loading Neuroscan CNT (.cnt) files"""
        # Arrange
        from scitex_io._load_modules._eeg import _load_eeg_data

        mock_raw = MagicMock()
        mock_mne.io.read_raw_cnt.return_value = mock_raw

        result = _load_eeg_data("neuroscan.cnt", montage="standard_1020")

        # Act
        mock_mne.io.read_raw_cnt.assert_called_once_with(
            "neuroscan.cnt", preload=True, montage="standard_1020"
        )
        # Assert
        assert result == mock_raw

    @patch("scitex_io._load_modules._eeg.mne")
    def test_egi_loading_result_equals_mock_raw(self, mock_mne):
        """Test loading EGI simple binary (.egi) files"""
        # Arrange
        from scitex_io._load_modules._eeg import _load_eeg_data

        mock_raw = MagicMock()
        mock_mne.io.read_raw_egi.return_value = mock_raw

        result = _load_eeg_data("egi_data.egi", include=["EEG 001", "EEG 002"])

        # Act
        mock_mne.io.read_raw_egi.assert_called_once_with(
            "egi_data.egi", preload=True, include=["EEG 001", "EEG 002"]
        )
        # Assert
        assert result == mock_raw

    @patch("scitex_io._load_modules._eeg.mne")
    def test_set_loading_result_equals_mock_raw(self, mock_mne):
        """Test loading EEGLAB SET (.set) files"""
        # Arrange
        from scitex_io._load_modules._eeg import _load_eeg_data

        mock_raw = MagicMock()
        mock_mne.io.read_raw.return_value = mock_raw

        result = _load_eeg_data("eeglab_data.set")

        # Act
        mock_mne.io.read_raw.assert_called_once_with("eeglab_data.set", preload=True)
        # Assert
        assert result == mock_raw

    @patch("scitex_io._load_modules._eeg.os.path.isfile")
    @patch("scitex_io._load_modules._eeg.mne")
    def test_eeg_brainvision_detection(self, mock_mne, mock_isfile):
        """Test .eeg file detection for BrainVision format"""
        # Arrange
        from scitex_io._load_modules._eeg import _load_eeg_data

        # Mock file existence - BrainVision files present
        def mock_file_exists(path):
            return path.endswith(".vhdr") or path.endswith(".vmrk")

        mock_isfile.side_effect = mock_file_exists

        mock_raw = MagicMock()
        mock_mne.io.read_raw_brainvision.return_value = mock_raw

        result = _load_eeg_data("data.eeg")

        # Should detect BrainVision and load .vhdr file
        # Act
        mock_mne.io.read_raw_brainvision.assert_called_once_with(
            "data.vhdr", preload=True
        )
        # Assert
        assert result == mock_raw

    @patch("scitex_io._load_modules._eeg.os.path.isfile")
    @patch("scitex_io._load_modules._eeg.mne")
    def test_eeg_nihon_koden_detection(self, mock_mne, mock_isfile):
        """Test .eeg file detection for Nihon Koden format"""
        # Arrange
        from scitex_io._load_modules._eeg import _load_eeg_data

        # Mock file existence - Nihon Koden files present
        def mock_file_exists(path):
            return (
                path.endswith(".21e") or path.endswith(".pnt") or path.endswith(".log")
            )

        mock_isfile.side_effect = mock_file_exists

        mock_raw = MagicMock()
        mock_mne.io.read_raw.return_value = mock_raw

        result = _load_eeg_data("nihon_data.eeg")

        # Should detect Nihon Koden and use generic reader
        # Act
        mock_mne.io.read_raw.assert_called_once_with("nihon_data.eeg", preload=True)
        # Assert
        assert result == mock_raw

    @patch("scitex_io._load_modules._eeg.mne")
    def test_mne_exception_propagation_raises_filenotfounderror(self, mock_mne):
        # Arrange
        # Arrange
        from scitex_io._load_modules._eeg import _load_eeg_data
        # Test file not found error
        # Act
        mock_mne.io.read_raw_edf.side_effect = FileNotFoundError("EDF file not found")
        # Act
        # Assert
        # Assert
        with pytest.raises(FileNotFoundError, match="EDF file not found"):
            _load_eeg_data("missing.edf")

    @patch("scitex_io._load_modules._eeg.mne")
    def test_mne_exception_propagation_raises_valueerror(self, mock_mne):
        # Arrange
        # Arrange
        from scitex_io._load_modules._eeg import _load_eeg_data
        # Test file not found error
        # Act
        mock_mne.io.read_raw_edf.side_effect = FileNotFoundError("EDF file not found")
        # Assert
        with pytest.raises(FileNotFoundError, match="EDF file not found"):
            _load_eeg_data("missing.edf")
        # Test invalid EEG data error
        mock_mne.io.read_raw_bdf.side_effect = ValueError("Invalid BDF format")
        # Act
        # Assert
        with pytest.raises(ValueError, match="Invalid BDF format"):
            _load_eeg_data("invalid.bdf")


    @patch("scitex_io._load_modules._eeg.mne")
    def test_kwargs_forwarding_calls_magicmock(self, mock_mne):
        """Test that kwargs are properly forwarded to MNE functions"""
        # Arrange
        # Act
        # Assert
        from scitex_io._load_modules._eeg import _load_eeg_data

        mock_raw = MagicMock()
        mock_mne.io.read_raw_edf.return_value = mock_raw

        # Test various kwargs
        kwargs = {
            "verbose": False,
            "stim_channel": "auto",
            "misc": ["ECG", "EOG"],
            "exclude": ["bad_channel"],
        }

        _load_eeg_data("test.edf", **kwargs)

        # Verify all kwargs were passed to MNE function
        mock_mne.io.read_raw_edf.assert_called_once_with(
            "test.edf", preload=True, **kwargs
        )

    @patch("scitex_io._load_modules._eeg.mne")
    def test_preload_always_true_kwargs_preload_is_true(self, mock_mne):
        # Arrange
        # Arrange
        from scitex_io._load_modules._eeg import _load_eeg_data
        mock_raw = MagicMock()
        mock_mne.io.read_raw_cnt.return_value = mock_raw
        # Even if user passes preload=False, it should be overridden to True
        _load_eeg_data("test.cnt", preload=False, verbose=True)
        # Verify preload=True was used
        # Act
        args, kwargs = mock_mne.io.read_raw_cnt.call_args
        # Act
        # Assert
        # Assert
        assert kwargs["preload"] is True

    @patch("scitex_io._load_modules._eeg.mne")
    def test_preload_always_true_kwargs_verbose_is_true(self, mock_mne):
        # Arrange
        # Arrange
        from scitex_io._load_modules._eeg import _load_eeg_data
        mock_raw = MagicMock()
        mock_mne.io.read_raw_cnt.return_value = mock_raw
        # Even if user passes preload=False, it should be overridden to True
        _load_eeg_data("test.cnt", preload=False, verbose=True)
        # Verify preload=True was used
        # Act
        args, kwargs = mock_mne.io.read_raw_cnt.call_args
        # Act
        # Assert
        # Assert
        assert kwargs["verbose"] is True


    def test_function_signature_lpath_in_sig_parameters(self):
        # Arrange
        # Arrange
        import inspect
        from scitex_io._load_modules._eeg import _load_eeg_data
        # Act
        sig = inspect.signature(_load_eeg_data)
        # Act
        # Assert
        # Assert
        assert "lpath" in sig.parameters

    def test_function_signature_kwargs_in_sig_parameters(self):
        # Arrange
        # Arrange
        import inspect
        from scitex_io._load_modules._eeg import _load_eeg_data
        # Act
        sig = inspect.signature(_load_eeg_data)
        # Act
        # Assert
        # Assert
        assert "kwargs" in sig.parameters

    def test_function_signature_sig_parameters_lpath_annotation_str(self):
        # Arrange
        # Arrange
        import inspect
        from scitex_io._load_modules._eeg import _load_eeg_data
        # Act
        sig = inspect.signature(_load_eeg_data)
        # Act
        # Assert
        # Assert
        assert sig.parameters["lpath"].annotation == str

    def test_function_signature_sig_return_annotation_inspect_signature_empty(self):
        # Arrange
        # Arrange
        import inspect
        from scitex_io._load_modules._eeg import _load_eeg_data
        # Act
        sig = inspect.signature(_load_eeg_data)
        # Act
        # Assert
        # Assert
        assert sig.return_annotation != inspect.Signature.empty


    def test_function_docstring_hasattr_load_eeg_data_doc(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io._load_modules._eeg import _load_eeg_data
        # Act
        # Assert
        # Assert
        assert hasattr(_load_eeg_data, "__doc__")

    def test_function_docstring_load_eeg_data_doc_is_not_none(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io._load_modules._eeg import _load_eeg_data
        # Act
        # Assert
        # Assert
        assert _load_eeg_data.__doc__ is not None

    def test_function_docstring_load_eeg_data_in_docstring(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io._load_modules._eeg import _load_eeg_data
        # Assert
        assert hasattr(_load_eeg_data, "__doc__")
        assert _load_eeg_data.__doc__ is not None
        docstring = _load_eeg_data.__doc__
        # Act
        # Assert
        assert "Load EEG data" in docstring

    def test_function_docstring_mne_python_in_docstring(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io._load_modules._eeg import _load_eeg_data
        # Assert
        assert hasattr(_load_eeg_data, "__doc__")
        assert _load_eeg_data.__doc__ is not None
        docstring = _load_eeg_data.__doc__
        # Act
        # Assert
        assert "MNE-Python" in docstring

    def test_function_docstring_brainvision_in_docstring(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io._load_modules._eeg import _load_eeg_data
        # Assert
        assert hasattr(_load_eeg_data, "__doc__")
        assert _load_eeg_data.__doc__ is not None
        docstring = _load_eeg_data.__doc__
        # Act
        # Assert
        assert "BrainVision" in docstring

    def test_function_docstring_edf_in_docstring(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io._load_modules._eeg import _load_eeg_data
        # Assert
        assert hasattr(_load_eeg_data, "__doc__")
        assert _load_eeg_data.__doc__ is not None
        docstring = _load_eeg_data.__doc__
        # Act
        # Assert
        assert "EDF" in docstring

    def test_function_docstring_parameters_in_docstring(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io._load_modules._eeg import _load_eeg_data
        # Assert
        assert hasattr(_load_eeg_data, "__doc__")
        assert _load_eeg_data.__doc__ is not None
        docstring = _load_eeg_data.__doc__
        # Act
        # Assert
        assert "Parameters" in docstring

    def test_function_docstring_returns_in_docstring(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io._load_modules._eeg import _load_eeg_data
        # Assert
        assert hasattr(_load_eeg_data, "__doc__")
        assert _load_eeg_data.__doc__ is not None
        docstring = _load_eeg_data.__doc__
        # Act
        # Assert
        assert "Returns" in docstring

    def test_function_docstring_raises_in_docstring(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io._load_modules._eeg import _load_eeg_data
        # Assert
        assert hasattr(_load_eeg_data, "__doc__")
        assert _load_eeg_data.__doc__ is not None
        docstring = _load_eeg_data.__doc__
        # Act
        # Assert
        assert "Raises" in docstring


    @patch("scitex_io._load_modules._eeg.mne")
    def test_warnings_suppression_calls_magicmock(self, mock_mne):
        """Test that runtime warnings are suppressed during loading"""
        # Arrange
        # Act
        # Assert
        import warnings

        from scitex_io._load_modules._eeg import _load_eeg_data

        mock_raw = MagicMock()
        mock_mne.io.read_raw_edf.return_value = mock_raw

        # Test that warnings are caught
        with patch(
            "scitex_io._load_modules._eeg.warnings.catch_warnings"
        ) as mock_catch:
            with patch(
                "scitex_io._load_modules._eeg.warnings.simplefilter"
            ) as mock_filter:
                _load_eeg_data("test.edf")

                mock_catch.assert_called_once()
                mock_filter.assert_called_once_with("ignore", RuntimeWarning)

    @patch("scitex_io._load_modules._eeg.mne")
    def test_real_world_eeg_scenarios_result_equals_mock_raw(self, mock_mne):
        # Arrange
        # Arrange
        from scitex_io._load_modules._eeg import _load_eeg_data
        # Scenario 1: Clinical EEG with 19 channels
        mock_raw = MagicMock()
        mock_raw.info = {
            "nchan": 19,
            "sfreq": 250.0,
            "ch_names": [
                "Fp1",
                "Fp2",
                "F3",
                "F4",
                "C3",
                "C4",
                "P3",
                "P4",
                "O1",
                "O2",
                "F7",
                "F8",
                "T3",
                "T4",
                "T5",
                "T6",
                "Fz",
                "Cz",
                "Pz",
            ],
        }
        mock_mne.io.read_raw_edf.return_value = mock_raw
        # Act
        result = _load_eeg_data("clinical_19ch.edf", stim_channel="auto")
        # Act
        # Assert
        # Assert
        assert result == mock_raw

    @patch("scitex_io._load_modules._eeg.mne")
    def test_real_world_eeg_scenarios_result_hd_equals_mock_raw_hd(self, mock_mne):
        # Arrange
        # Arrange
        from scitex_io._load_modules._eeg import _load_eeg_data
        # Scenario 1: Clinical EEG with 19 channels
        mock_raw = MagicMock()
        mock_raw.info = {
            "nchan": 19,
            "sfreq": 250.0,
            "ch_names": [
                "Fp1",
                "Fp2",
                "F3",
                "F4",
                "C3",
                "C4",
                "P3",
                "P4",
                "O1",
                "O2",
                "F7",
                "F8",
                "T3",
                "T4",
                "T5",
                "T6",
                "Fz",
                "Cz",
                "Pz",
            ],
        }
        mock_mne.io.read_raw_edf.return_value = mock_raw
        # Act
        result = _load_eeg_data("clinical_19ch.edf", stim_channel="auto")
        # Assert
        assert result == mock_raw
        mock_mne.io.read_raw_edf.assert_called_with(
            "clinical_19ch.edf", preload=True, stim_channel="auto"
        )
        # Scenario 2: High-density EEG with 128 channels
        mock_raw_hd = MagicMock()
        mock_raw_hd.info = {"nchan": 128, "sfreq": 500.0}
        mock_mne.io.read_raw_egi.return_value = mock_raw_hd
        result_hd = _load_eeg_data("highdensity_128ch.egi", montage=None)
        # Act
        # Assert
        assert result_hd == mock_raw_hd


    @patch("scitex_io._load_modules._eeg.mne")
    def test_extension_extraction_edge_cases(self, mock_mne):
        """Test edge cases in file extension extraction"""
        # Arrange
        # Act
        # Assert
        from scitex_io._load_modules._eeg import _load_eeg_data

        mock_raw = MagicMock()
        mock_mne.io.read_raw_edf.return_value = mock_raw

        # Test files with multiple dots
        test_files = ["file.with.dots.edf", "data.v1.0.bdf", "experiment.session1.gdf"]

        for test_file in test_files:
            mock_mne.reset_mock()
            _load_eeg_data(test_file)

            # Should extract the last extension correctly
            if test_file.endswith(".edf"):
                mock_mne.io.read_raw_edf.assert_called_once()
            elif test_file.endswith(".bdf"):
                mock_mne.io.read_raw_bdf.assert_called_once()
            elif test_file.endswith(".gdf"):
                mock_mne.io.read_raw_gdf.assert_called_once()

    def test_case_sensitive_extension_check(self):
        """Test case sensitivity of extensions"""
        # Arrange
        # Act
        # Assert
        from scitex_io._load_modules._eeg import _load_eeg_data

        # Test uppercase extensions (should fail)
        uppercase_files = ["file.EDF", "data.BDF", "test.CNT"]

        for test_file in uppercase_files:
            with pytest.raises(
                ValueError, match="File must have one of these extensions"
            ):
                _load_eeg_data(test_file)

    @patch("scitex_io._load_modules._eeg.os.path.isfile")
    @patch("scitex_io._load_modules._eeg.mne")
    def test_eeg_extension_no_associated_files(self, mock_mne, mock_isfile):
        """Test .eeg file handling when no associated files are found"""
        # Arrange
        from scitex_io._load_modules._eeg import _load_eeg_data

        # Mock no associated files found
        # Act
        mock_isfile.return_value = False

        # Should raise an error for .eeg without associated files
        # Assert
        with pytest.raises(ValueError, match="No associated files found for .eeg file"):
            _load_eeg_data("standalone.eeg")


if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])

# --------------------------------------------------------------------------------
# Start of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_load_modules/_eeg.py
# --------------------------------------------------------------------------------
# #!/usr/bin/env python3
# # Time-stamp: "2024-11-14 07:56:27 (ywatanabe)"
# # File: ./scitex_repo/src/scitex/io/_load_modules/_eeg.py
#
# import os
# import warnings
# from typing import Any
#
# try:
#     import mne
#
#     MNE_AVAILABLE = True
# except ImportError:
#     MNE_AVAILABLE = False
#     mne = None
#
#
# def _load_eeg_data(lpath: str, **kwargs) -> Any:
#     """
#     Load EEG data based on file extension and associated files using MNE-Python.
#
#     This function supports various EEG file formats including BrainVision, EDF, BDF, GDF, CNT, EGI, and SET.
#     It also handles special cases for .eeg files (BrainVision and Nihon Koden).
#
#     Parameters:
#     -----------
#     lpath : str
#         The path to the EEG file to be loaded.
#     **kwargs : dict
#         Additional keyword arguments to be passed to the specific MNE loading function.
#
#     Returns:
#     --------
#     raw : mne.io.Raw
#         The loaded raw EEG data.
#
#     Raises:
#     -------
#     ValueError
#         If the file extension is not supported.
#
#     Notes:
#     ------
#     This function uses MNE-Python to load the EEG data. It automatically detects the file format
#     based on the file extension and uses the appropriate MNE function to load the data.
#     """
#     if not MNE_AVAILABLE:
#         raise ImportError(
#             "MNE-Python is not installed. Please install with: pip install mne"
#         )
#
#     # Get the file extension
#     extension = lpath.split(".")[-1]
#
#     allowed_extensions = [
#         "vhdr",
#         "vmrk",
#         "edf",
#         "bdf",
#         "gdf",
#         "cnt",
#         "egi",
#         "eeg",
#         "set",
#     ]
#
#     if extension not in allowed_extensions:
#         raise ValueError(
#             f"File must have one of these extensions: {', '.join(allowed_extensions)}"
#         )
#
#     # Remove preload from kwargs if present - we always use preload=True
#     kwargs.pop("preload", None)
#
#     with warnings.catch_warnings():
#         warnings.simplefilter("ignore", RuntimeWarning)
#
#         # Load the data based on the file extension
#         if extension in ["vhdr", "vmrk"]:
#             # Load BrainVision data
#             raw = mne.io.read_raw_brainvision(lpath, preload=True, **kwargs)
#         elif extension == "edf":
#             # Load European data format
#             raw = mne.io.read_raw_edf(lpath, preload=True, **kwargs)
#         elif extension == "bdf":
#             # Load BioSemi data format
#             raw = mne.io.read_raw_bdf(lpath, preload=True, **kwargs)
#         elif extension == "gdf":
#             # Load Gen data format
#             raw = mne.io.read_raw_gdf(lpath, preload=True, **kwargs)
#         elif extension == "cnt":
#             # Load Neuroscan CNT data
#             raw = mne.io.read_raw_cnt(lpath, preload=True, **kwargs)
#         elif extension == "egi":
#             # Load EGI simple binary data
#             raw = mne.io.read_raw_egi(lpath, preload=True, **kwargs)
#         elif extension == "set":
#             # ???
#             raw = mne.io.read_raw(lpath, preload=True, **kwargs)
#         elif extension == "eeg":
#             is_BrainVision = any(
#                 os.path.isfile(lpath.replace(".eeg", ext)) for ext in [".vhdr", ".vmrk"]
#             )
#             is_NihonKoden = any(
#                 os.path.isfile(lpath.replace(".eeg", ext))
#                 for ext in [".21e", ".pnt", ".log"]
#             )
#
#             # Brain Vision
#             if is_BrainVision:
#                 lpath_v = lpath.replace(".eeg", ".vhdr")
#                 raw = mne.io.read_raw_brainvision(lpath_v, preload=True, **kwargs)
#             # Nihon Koden
#             elif is_NihonKoden:
#                 # raw = mne.io.read_raw_nihon(lpath, preload=True, **kwargs)
#                 raw = mne.io.read_raw(lpath, preload=True, **kwargs)
#             else:
#                 raise ValueError("No associated files found for .eeg file")
#         else:
#             raise ValueError(f"Unsupported file extension: {extension}")
#
#         return raw
#
#
# # EOF

# --------------------------------------------------------------------------------
# End of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_load_modules/_eeg.py
# --------------------------------------------------------------------------------
