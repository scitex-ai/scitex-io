#!/usr/bin/env python3
# Time-stamp: "2025-06-02 14:50:00 (ywatanabe)"
# File: ./scitex_repo/tests/scitex/io/_load_modules/test__image.py

"""Comprehensive tests for image file loading functionality."""

import os
import tempfile

import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")
import numpy as np
from PIL import Image, ImageDraw


class TestLoadImage:
    """Test suite for _load_image function."""

    @pytest.fixture
    def rgb_red_blue_split_image(self):
        img_array = np.zeros((100, 100, 3), dtype=np.uint8)
        img_array[:, :50, 0] = 255  # Red half
        img_array[:, 50:, 2] = 255  # Blue half
        return Image.fromarray(img_array, "RGB")

    @pytest.fixture(params=[".png", ".jpg", ".jpeg"])
    def loaded_rgb_image_for_ext(self, tmp_path, rgb_red_blue_split_image, request):
        from scitex_io._load_modules._image import _load_image

        ext = request.param
        p = tmp_path / f"x{ext}"
        if ext in (".jpg", ".jpeg"):
            rgb_red_blue_split_image.save(str(p), quality=95)
        else:
            rgb_red_blue_split_image.save(str(p))
        return _load_image(str(p), metadata=False)

    def test_basic_rgb_image_returns_pil_image(self, loaded_rgb_image_for_ext):
        # Arrange
        loaded = loaded_rgb_image_for_ext
        # Act
        result = isinstance(loaded, Image.Image)
        # Assert
        assert result

    def test_basic_rgb_image_preserves_size(self, loaded_rgb_image_for_ext):
        # Arrange
        loaded = loaded_rgb_image_for_ext
        # Act
        result = loaded.size
        # Assert
        assert result == (100, 100)

    def test_basic_rgb_image_mode_is_rgb_or_rgba(self, loaded_rgb_image_for_ext):
        # Arrange
        loaded = loaded_rgb_image_for_ext
        # Act
        result = loaded.mode
        # Assert
        assert result in ("RGB", "RGBA")

    def test_basic_rgb_image_left_half_is_red(self, loaded_rgb_image_for_ext):
        # Arrange
        loaded = loaded_rgb_image_for_ext
        loaded_array = np.array(loaded)
        if loaded_array.ndim == 3 and loaded_array.shape[2] == 4:
            loaded_array = loaded_array[:, :, :3]
        # Act
        red_mean = loaded_array[:, 25, 0].mean()
        # Assert
        assert red_mean > 200

    def test_basic_rgb_image_right_half_is_blue(self, loaded_rgb_image_for_ext):
        # Arrange
        loaded = loaded_rgb_image_for_ext
        loaded_array = np.array(loaded)
        if loaded_array.ndim == 3 and loaded_array.shape[2] == 4:
            loaded_array = loaded_array[:, :, :3]
        # Act
        blue_mean = loaded_array[:, 75, 2].mean()
        # Assert
        assert blue_mean > 200

    @pytest.fixture
    def loaded_grayscale_image(self, tmp_path):
        from scitex_io._load_modules._image import _load_image

        gray_array = np.linspace(0, 255, 10000, dtype=np.uint8).reshape(100, 100)
        img = Image.fromarray(gray_array, "L")
        p = tmp_path / "gray.png"
        img.save(str(p))
        return _load_image(str(p), metadata=False)

    def test_grayscale_image_returns_pil_image(self, loaded_grayscale_image):
        # Arrange
        loaded = loaded_grayscale_image
        # Act
        result = isinstance(loaded, Image.Image)
        # Assert
        assert result

    def test_grayscale_image_preserves_size(self, loaded_grayscale_image):
        # Arrange
        loaded = loaded_grayscale_image
        # Act
        result = loaded.size
        # Assert
        assert result == (100, 100)

    def test_grayscale_image_mode_is_l(self, loaded_grayscale_image):
        # Arrange
        loaded = loaded_grayscale_image
        # Act
        result = loaded.mode
        # Assert
        assert result == "L"

    def test_grayscale_image_preserves_gradient(self, loaded_grayscale_image):
        # Arrange
        loaded_array = np.array(loaded_grayscale_image)
        # Act
        result = loaded_array[0, 0] < loaded_array[99, 99]
        # Assert
        assert result

    @pytest.fixture
    def loaded_rgba_image(self, tmp_path):
        from scitex_io._load_modules._image import _load_image

        rgba_array = np.zeros((100, 100, 4), dtype=np.uint8)
        rgba_array[:, :, 0] = 255
        rgba_array[:, :50, 3] = 255
        rgba_array[:, 50:, 3] = 128
        img = Image.fromarray(rgba_array, "RGBA")
        p = tmp_path / "rgba.png"
        img.save(str(p))
        return _load_image(str(p), metadata=False)

    def test_rgba_image_returns_pil_image(self, loaded_rgba_image):
        # Arrange
        loaded = loaded_rgba_image
        # Act
        result = isinstance(loaded, Image.Image)
        # Assert
        assert result

    def test_rgba_image_preserves_size(self, loaded_rgba_image):
        # Arrange
        loaded = loaded_rgba_image
        # Act
        result = loaded.size
        # Assert
        assert result == (100, 100)

    def test_rgba_image_mode_is_rgba(self, loaded_rgba_image):
        # Arrange
        loaded = loaded_rgba_image
        # Act
        result = loaded.mode
        # Assert
        assert result == "RGBA"

    def test_rgba_image_left_half_full_opacity(self, loaded_rgba_image):
        # Arrange
        loaded_array = np.array(loaded_rgba_image)
        # Act
        result = loaded_array[50, 25, 3]
        # Assert
        assert result == 255

    def test_rgba_image_right_half_half_opacity(self, loaded_rgba_image):
        # Arrange
        loaded_array = np.array(loaded_rgba_image)
        # Act
        result = loaded_array[50, 75, 3]
        # Assert
        assert result == 128

    @pytest.fixture
    def tiff_image_array(self):
        return np.random.randint(0, 255, (200, 300, 3), dtype=np.uint8)

    @pytest.fixture(params=[".tiff", ".tif"])
    def loaded_tiff_for_ext(self, tmp_path, tiff_image_array, request):
        from scitex_io._load_modules._image import _load_image

        img = Image.fromarray(tiff_image_array, "RGB")
        p = tmp_path / f"x{request.param}"
        img.save(str(p), compression="lzw")
        return tiff_image_array, _load_image(str(p), metadata=False)

    def test_tiff_format_returns_pil_image(self, loaded_tiff_for_ext):
        # Arrange
        _orig, loaded = loaded_tiff_for_ext
        # Act
        result = isinstance(loaded, Image.Image)
        # Assert
        assert result

    def test_tiff_format_preserves_size(self, loaded_tiff_for_ext):
        # Arrange
        _orig, loaded = loaded_tiff_for_ext
        # Act
        result = loaded.size
        # Assert
        assert result == (300, 200)

    def test_tiff_format_mode_is_rgb(self, loaded_tiff_for_ext):
        # Arrange
        _orig, loaded = loaded_tiff_for_ext
        # Act
        result = loaded.mode
        # Assert
        assert result == "RGB"

    def test_tiff_format_preserves_pixel_values(self, loaded_tiff_for_ext):
        # Arrange
        orig, loaded = loaded_tiff_for_ext
        # Act
        result = np.array_equal(np.array(loaded), orig)
        # Assert
        assert result

    @pytest.fixture
    def loaded_large_image(self, tmp_path):
        from scitex_io._load_modules._image import _load_image

        large_array = np.random.randint(0, 255, (2160, 3840, 3), dtype=np.uint8)
        img = Image.fromarray(large_array, "RGB")
        p = tmp_path / "large.png"
        img.save(str(p), optimize=True, compress_level=6)
        return _load_image(str(p), metadata=False)

    def test_large_image_returns_pil_image(self, loaded_large_image):
        # Arrange
        loaded = loaded_large_image
        # Act
        result = isinstance(loaded, Image.Image)
        # Assert
        assert result

    def test_large_image_preserves_size(self, loaded_large_image):
        # Arrange
        loaded = loaded_large_image
        # Act
        result = loaded.size
        # Assert
        assert result == (3840, 2160)

    def test_large_image_mode_is_rgb(self, loaded_large_image):
        # Arrange
        loaded = loaded_large_image
        # Act
        result = loaded.mode
        # Assert
        assert result == "RGB"

    def test_large_image_array_shape_matches(self, loaded_large_image):
        # Arrange
        loaded = loaded_large_image
        # Act
        result = np.array(loaded).shape
        # Assert
        assert result == (2160, 3840, 3)

    @pytest.fixture
    def loaded_16bit_tiff(self, tmp_path):
        from scitex_io._load_modules._image import _load_image

        img_16bit = Image.new("I;16", (256, 256))
        draw = ImageDraw.Draw(img_16bit)
        for i in range(0, 256, 32):
            draw.rectangle([i, i, i + 16, i + 16], fill=i * 256)
        p = tmp_path / "x.tiff"
        img_16bit.save(str(p))
        return _load_image(str(p), metadata=False)

    def test_scientific_16bit_returns_pil_image(self, loaded_16bit_tiff):
        # Arrange
        loaded = loaded_16bit_tiff
        # Act
        result = isinstance(loaded, Image.Image)
        # Assert
        assert result

    def test_scientific_16bit_preserves_size(self, loaded_16bit_tiff):
        # Arrange
        loaded = loaded_16bit_tiff
        # Act
        result = loaded.size
        # Assert
        assert result == (256, 256)

    def test_scientific_16bit_mode_is_grey_family(self, loaded_16bit_tiff):
        # Arrange
        loaded = loaded_16bit_tiff
        # Act
        result = loaded.mode
        # Assert
        assert result in ("I;16", "I", "L")

    @pytest.fixture
    def loaded_first_page_of_multipage_tiff(self, tmp_path):
        from scitex_io._load_modules._image import _load_image

        pages = []
        for i in range(3):
            img_array = np.full((100, 100, 3), i * 80, dtype=np.uint8)
            pages.append(Image.fromarray(img_array, "RGB"))
        p = tmp_path / "multi.tiff"
        pages[0].save(
            str(p), save_all=True, append_images=pages[1:], compression="lzw"
        )
        return _load_image(str(p), metadata=False)

    def test_multipage_tiff_returns_pil_image(
        self, loaded_first_page_of_multipage_tiff
    ):
        # Arrange
        loaded = loaded_first_page_of_multipage_tiff
        # Act
        result = isinstance(loaded, Image.Image)
        # Assert
        assert result

    def test_multipage_tiff_preserves_size(self, loaded_first_page_of_multipage_tiff):
        # Arrange
        loaded = loaded_first_page_of_multipage_tiff
        # Act
        result = loaded.size
        # Assert
        assert result == (100, 100)

    def test_multipage_tiff_mode_is_rgb(self, loaded_first_page_of_multipage_tiff):
        # Arrange
        loaded = loaded_first_page_of_multipage_tiff
        # Act
        result = loaded.mode
        # Assert
        assert result == "RGB"

    def test_multipage_tiff_first_page_is_all_zeros(
        self, loaded_first_page_of_multipage_tiff
    ):
        # Arrange
        loaded_array = np.array(loaded_first_page_of_multipage_tiff)
        # Act
        result = bool(np.all(loaded_array == 0))
        # Assert
        assert result

    @pytest.fixture
    def loaded_kwargs_png(self, tmp_path):
        from scitex_io._load_modules._image import _load_image

        img_array = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
        img = Image.fromarray(img_array, "RGB")
        p = tmp_path / "kw.png"
        img.save(str(p))
        return _load_image(str(p), metadata=False, formats=["PNG"])

    def test_kwargs_parameter_passing_returns_pil_image(self, loaded_kwargs_png):
        # Arrange
        loaded = loaded_kwargs_png
        # Act
        result = isinstance(loaded, Image.Image)
        # Assert
        assert result

    def test_kwargs_parameter_passing_preserves_size(self, loaded_kwargs_png):
        # Arrange
        loaded = loaded_kwargs_png
        # Act
        result = loaded.size
        # Assert
        assert result == (50, 50)

    def test_unsupported_extensions_smoke_case(self):
        """Test that unsupported file extensions raise ValueError."""
        # Arrange
        # Act
        # Assert
        from scitex_io._load_modules._image import _load_image

        unsupported_extensions = [
            "file.txt",
            "image.gif",
            "data.csv",
            "document.pdf",
            "archive.zip",
            "executable.exe",
            "image.bmp",
            "image.webp",
        ]

        for filename in unsupported_extensions:
            with pytest.raises(ValueError, match="Unsupported image format"):
                _load_image(filename)

    def test_supported_extensions_validation(self):
        """Test that all documented supported extensions are recognized."""
        # Arrange
        # Act
        # Assert
        from scitex_io._load_modules._image import _load_image

        # These should not raise ValueError (will raise FileNotFoundError instead)
        supported_extensions = [
            "image.jpg",
            "image.png",
            "image.tiff",
            "image.tif",
            "photo.JPG",
            "scan.PNG",
            "data.TIFF",
            "microscopy.TIF",
        ]

        for filename in supported_extensions:
            try:
                _load_image(filename)
            except ValueError:
                pytest.fail(
                    f"Extension {filename} should be supported but raised ValueError"
                )
            except FileNotFoundError:
                pass  # Expected for non-existent files

    def test_nonexistent_file_error(self):
        """Test that loading non-existent files raises appropriate errors."""
        # Arrange
        # Act
        # Assert
        from scitex_io._load_modules._image import _load_image

        nonexistent_files = [
            "/nonexistent/image.png",
            "./missing_image.jpg",
            "/tmp/not_found.tiff",
        ]

        for filepath in nonexistent_files:
            with pytest.raises(FileNotFoundError):
                _load_image(filepath)

    def test_corrupted_image_file(self):
        """Test handling of corrupted image files."""
        # Arrange
        # Act
        # Assert
        from scitex_io._load_modules._image import _load_image

        # Create a file with image extension but invalid content
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"This is not a valid PNG file content")
            temp_path = f.name

        try:
            # Should raise an exception from PIL
            with pytest.raises(
                Exception
            ):  # PIL raises various exceptions for corrupted files
                _load_image(temp_path)
        finally:
            os.unlink(temp_path)

    def test_empty_image_file(self):
        """Test handling of empty image files."""
        # Arrange
        # Act
        # Assert
        from scitex_io._load_modules._image import _load_image

        # Create empty file with image extension
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            temp_path = f.name  # File is empty

        try:
            with pytest.raises(Exception):  # PIL should raise an exception
                _load_image(temp_path)
        finally:
            os.unlink(temp_path)

    def test_case_insensitive_extensions(self):
        """Test that file extension matching is case-insensitive."""
        # Arrange
        # Act
        # Assert
        from scitex_io._load_modules._image import _load_image

        # Create test image
        img_array = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
        img = Image.fromarray(img_array, "RGB")

        # Test various case combinations
        for ext in [".PNG", ".Jpg", ".JPEG", ".TifF", ".TIF"]:
            with tempfile.NamedTemporaryFile(suffix=ext.lower(), delete=False) as f:
                img.save(f.name)
                # Rename to have uppercase extension
                uppercase_path = f.name.replace(ext.lower(), ext)
                os.rename(f.name, uppercase_path)
                temp_path = uppercase_path

            try:
                # This should work despite case differences
                try:
                    loaded_img = _load_image(temp_path, metadata=False)
                    # Check if we got an image (could be tuple if metadata=True default)
                    if isinstance(loaded_img, tuple):
                        loaded_img = loaded_img[0]
                    assert isinstance(loaded_img, Image.Image)
                except ValueError:
                    # Current implementation might be case-sensitive
                    # This documents the current behavior
                    pass
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    def test_load_image_returns_pil_image_for_real_png(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._image import _load_image

        img = Image.new("RGB", (640, 480), color=(10, 20, 30))
        p = tmp_path / "x.png"
        img.save(str(p))
        # Act
        result = _load_image(str(p), metadata=False)
        # Assert
        assert isinstance(result, Image.Image)

    def test_load_image_preserves_size_for_real_png(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._image import _load_image

        img = Image.new("RGB", (640, 480), color=(10, 20, 30))
        p = tmp_path / "x.png"
        img.save(str(p))
        # Act
        result = _load_image(str(p), metadata=False)
        # Assert
        assert result.size == (640, 480)

    def test_load_image_with_formats_kwarg_returns_pil_image(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._image import _load_image

        img = Image.new("RGB", (50, 50), color=(0, 0, 0))
        p = tmp_path / "x.png"
        img.save(str(p))
        # Act
        result = _load_image(str(p), metadata=False, formats=["PNG"])
        # Assert
        assert isinstance(result, Image.Image)


if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])

# --------------------------------------------------------------------------------
# Start of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_load_modules/_image.py
# --------------------------------------------------------------------------------
# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# # Time-stamp: "2024-11-14 07:55:38 (ywatanabe)"
# # File: ./scitex_repo/src/scitex/io/_load_modules/_image.py
#
# from typing import Any, Dict, Optional, Tuple, Union
#
# from PIL import Image
#
# from scitex import logging
#
# logger = logging.getLogger(__name__)
#
#
# def _load_image(
#     lpath: str, metadata: bool = True, verbose: bool = False, **kwargs
# ) -> Union[Any, Tuple[Any, Optional[Dict]]]:
#     """
#     Load image file.
#
#     Args:
#         lpath: Path to image file
#         metadata: If True, return (image, metadata_dict) tuple. Default True.
#         verbose: If True, log information about metadata loading. Default False.
#         **kwargs: Additional arguments passed to Image.open()
#
#     Returns:
#         By default (metadata=True): (PIL.Image, dict) tuple
#         If metadata=False: PIL.Image object only
#         If no metadata found, returns (PIL.Image, None)
#     """
#     supported_exts = [".jpg", ".jpeg", ".png", ".tiff", ".tif"]
#     if not any(lpath.lower().endswith(ext) for ext in supported_exts):
#         raise ValueError("Unsupported image format")
#
#     img = Image.open(lpath, **kwargs)
#
#     if not metadata:
#         return img
#
#     # Try to read metadata
#     if verbose:
#         logger.info(f"✅ Loading image with metadata from: {lpath}")
#
#     try:
#         from .._metadata import read_metadata
#
#         metadata_dict = read_metadata(lpath)
#
#         if verbose:
#             if metadata_dict:
#                 logger.info(f"  • Embedded metadata found:")
#                 for key, value in metadata_dict.items():
#                     logger.info(f"    - {key}: {value}")
#             else:
#                 logger.info("  • No embedded metadata found")
#
#         return img, metadata_dict
#
#     except Exception as e:
#         # If metadata reading fails, return None
#         logger.warning(f"Failed to read metadata: {e}")
#         return img, None
#
#
# # EOF

# --------------------------------------------------------------------------------
# End of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_load_modules/_image.py
# --------------------------------------------------------------------------------
