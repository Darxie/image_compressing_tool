import os
import io
import pytest
from PIL import Image

from main import compress, main


@pytest.fixture
def sample_image_path(tmp_path):
    """
    Create a temporary PNG image to use for testing and return its file path.
    """
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))  # 100x100 red image
    path = tmp_path / "test_image.png"
    img.save(path, format="PNG")
    return path


@pytest.fixture
def non_image_file(tmp_path):
    """
    Create a temporary text file that is NOT an image, for negative testing.
    """
    path = tmp_path / "not_an_image.txt"
    path.write_text("Just some text, not a valid image file!")
    return path


# -------------------------------------------------------------------
# Unit Tests for compress()
# -------------------------------------------------------------------

def test_compress_returns_bytes(sample_image_path):
    compressed_data = compress(str(sample_image_path), quality=85)
    assert isinstance(compressed_data, bytes), "compress() should return bytes."


def test_compress_output_is_jpeg(sample_image_path):
    compressed_data = compress(str(sample_image_path), quality=85)
    with io.BytesIO(compressed_data) as buf:
        img = Image.open(buf)
        assert img.format == "JPEG", "compress() should produce a JPEG."


def test_compress_respects_quality(sample_image_path):
    data_30 = compress(str(sample_image_path), quality=30)
    data_90 = compress(str(sample_image_path), quality=90)
    # Typically, lower quality => smaller file
    assert len(data_30) < len(data_90), (
        "Lower-quality compression should produce smaller file size."
    )


def test_compress_raises_file_not_found_error():
    """
    If you want compress() to raise an error when the file is missing,
    here's a test for it. Adjust if you handle this differently.
    """
    with pytest.raises(FileNotFoundError):
        compress("non_existent_file.png")


def test_compress_non_image_file(non_image_file):
    """
    If your code attempts to load a file that's not an image,
    Pillow will raise an OSError by default. Adjust if you handle it differently.
    """
    with pytest.raises(OSError):
        compress(str(non_image_file))


# -------------------------------------------------------------------
# Integration / Acceptance Tests for main()
# -------------------------------------------------------------------

def test_main_creates_compressed_file(sample_image_path, monkeypatch, capsys):
    """
    Simulate a CLI call to main() with valid arguments.
    """
    output_path = sample_image_path.parent / "compressed_output.jpg"
    test_args = [
        "prog",  # placeholder for sys.argv[0]
        str(sample_image_path),
        "--quality", "50",
        "--output_file", str(output_path)
    ]
    monkeypatch.setattr("sys.argv", test_args)

    main()

    captured = capsys.readouterr()
    assert f"Compressed image saved at {output_path}" in captured.out, (
        "Expected success message on stdout."
    )
    assert output_path.exists(), "Output file should be created by main()"
    assert os.path.getsize(output_path) > 0, "Output file should not be empty"


def test_main_uses_default_quality(sample_image_path, monkeypatch, capsys):
    """
    If the user doesn't specify --quality, check that main() uses its default.
    (This test assumes your default is 85; change as needed.)
    """
    output_path = sample_image_path.parent / "default_quality_output.jpg"
    test_args = [
        "prog",
        str(sample_image_path),
        "--output_file", str(output_path)
        # no --quality arg
    ]
    monkeypatch.setattr("sys.argv", test_args)

    main()

    captured = capsys.readouterr()
    # If your main() prints the used quality, you can assert on it:
    # assert "Using default quality: 85" in captured.out  # for example
    assert output_path.exists(), "File should be created even without explicit --quality"


def test_main_uses_default_output_name(sample_image_path, monkeypatch, capsys):
    """
    Check that if the user doesn't specify --output_file,
    main() generates a default output path.
    """
    test_args = [
        "prog",
        str(sample_image_path),
        "--quality", "60"
        # no --output_file
    ]
    monkeypatch.setattr("sys.argv", test_args)

    main()

    captured = capsys.readouterr()
    # e.g., maybe default file is <original_basename>_compressed.jpg
    # If your code prints that path in stdout, you can parse it. For example:
    assert "Compressed image saved at" in captured.out

    # If needed, extract the path from stdout to do further checks:
    # lines = captured.out.splitlines()
    # last_line = lines[-1]  # "Compressed image saved at xyz..."
    # etc.


def test_main_missing_input_file(monkeypatch, capsys):
    """
    If the user doesn't provide an input file, does main() handle it gracefully?
    This depends on how your code is set up.
    """
    test_args = [
        "prog",
        # missing input file arg
    ]
    monkeypatch.setattr("sys.argv", test_args)

    with pytest.raises(SystemExit) as exc:
        main()

    captured = capsys.readouterr()
    assert exc.value.code != 0, "main() should exit with a non-zero error code."
    assert "error" in captured.err.lower() or "usage" in captured.out.lower(), (
        "Expect an error or usage message when no input file is provided."
    )


def test_main_with_non_image_file(non_image_file, monkeypatch, capsys):
    """
    If someone passes a file that isn't an image, see if main() handles it gracefully.
    """
    test_args = [
        "prog",
        str(non_image_file)
    ]
    monkeypatch.setattr("sys.argv", test_args)

    with pytest.raises(SystemExit) as exc:
        main()

    captured = capsys.readouterr()
    assert exc.value.code != 0, "Non-image input should cause an error exit."
    assert "not a valid image" in captured.out.lower() or "error" in captured.out.lower(), (
        "Expected an error message about the file not being an image."
    )


def test_main_prints_help(monkeypatch, capsys):
    """
    If the user runs the script with --help, verify that help text is displayed.
    """
    test_args = ["prog", "--help"]
    monkeypatch.setattr("sys.argv", test_args)

    # Typically argparse will SystemExit after printing help:
    with pytest.raises(SystemExit) as exc:
        main()
    captured = capsys.readouterr()

    assert exc.value.code == 0, "--help should exit with code 0"
    assert "usage:" in captured.out.lower(), "Help text should mention 'usage:'"
    assert "quality" in captured.out.lower(), "Help text should mention 'quality'"
    assert "output_file" in captured.out.lower(), "Help text should mention 'output_file'"

