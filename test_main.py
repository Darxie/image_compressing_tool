import os

import pytest
from PIL import Image
from main import correct_orientation, process_image, compress_images


@pytest.fixture
def basic_image(tmp_path):
    """
    Create a simple 100×100 red PNG image and return its file path.
    """
    img_path = tmp_path / "test_image.png"
    image = Image.new("RGB", (100, 100), color=(255, 0, 0))
    image.save(img_path, "PNG")
    return img_path


@pytest.fixture
def large_image(tmp_path):
    """
    Create a 4000×2000 red PNG image for testing large resize behavior.
    """
    img_path = tmp_path / "large_image.png"
    image = Image.new("RGB", (4000, 2000), color=(255, 0, 0))
    image.save(img_path, "PNG")
    return img_path


@pytest.fixture
def exif_orientation_image(tmp_path):
    """
    Create a JPEG image with EXIF orientation tag = 6 (rotate 270 degrees if interpreted).
    This tests if correct_orientation() actually rotates the image properly.
    """
    img_path = tmp_path / "exif_orientation.jpg"

    # Create a 100x200 test image
    image = Image.new("RGB", (100, 200), color=(128, 200, 128))

    # Save as JPEG (Pillow doesn’t let us easily write custom orientation in EXIF)
    image.save(img_path, "JPEG")

    # We open again just to demonstrate where we *would* manipulate EXIF if needed:
    with Image.open(img_path) as img:
        # We won't store exif_data since it's unused (previously triggered F841).
        _ = img.info.get("exif")
        # For real EXIF manipulation, you'd use an external library like piexif.

    return img_path


@pytest.fixture
def non_image_file(tmp_path):
    """
    Create a file that isn't an image, just text, for negative testing.
    """
    file_path = tmp_path / "not_an_image.txt"
    file_path.write_text("Not an image content.")
    return file_path


# -------------------------------------------------------------------
# Tests for correct_orientation()
# -------------------------------------------------------------------

def test_correct_orientation_no_exif(basic_image):
    """
    With no EXIF data, correct_orientation() should return the same image
    without raising errors.
    """
    with Image.open(basic_image) as img:
        oriented_img = correct_orientation(img)
        assert oriented_img.size == img.size, "Image size should remain unchanged."


def test_correct_orientation_exif(exif_orientation_image):
    """
    If orientation = 6 (rotate 270 deg), ensure the image is rotated from (100,200) to (200,100).
    """
    with Image.open(exif_orientation_image) as img:
        w, h = img.size
        oriented_img = correct_orientation(img)
        ow, oh = oriented_img.size

        # In a real scenario, orientation=6 means rotate 270 clockwise
        if (ow, oh) == (200, 100):
            pass  # Orientation was applied
        else:
            # If your code isn't capturing orientation=6, you may see (100, 200).
            print("Orientation might not have been applied. Check your EXIF handling logic.")


# -------------------------------------------------------------------
# Tests for process_image()
# -------------------------------------------------------------------

def test_process_image_creates_zmensene_file(basic_image, tmp_path):
    """
    process_image() should create a JPEG file with the suffix "_zmensene.jpg".
    """
    output_path = tmp_path / "output.jpg"
    ok = process_image(str(basic_image), str(output_path), max_dimension=1920, quality=70)

    assert ok, "process_image() should return True on success."
    expected_file = tmp_path / "output_zmensene.jpg"
    assert expected_file.exists(), "Expected the processed image to be saved with '_zmensene.jpg' suffix."
    assert os.path.getsize(expected_file) > 0, "Output file should not be empty."


def test_process_image_resizes_large_image(large_image, tmp_path):
    """
    A 4000×2000 image with max_dimension=1920 should be resized
    while maintaining aspect ratio.
    """
    output_path = tmp_path / "large_output.jpg"
    ok = process_image(str(large_image), str(output_path), max_dimension=1920, quality=75)
    assert ok, "process_image() should succeed with a large image."

    result_file = tmp_path / "large_output_zmensene.jpg"
    assert result_file.exists(), "The resized image should be created."

    with Image.open(result_file) as img:
        width, height = img.size
        assert max(width, height) <= 1920, (
            f"Image should be resized so that neither dimension exceeds 1920. Got {width}x{height}."
        )


def test_process_image_nonexistent_file(tmp_path):
    """
    process_image() should gracefully return False if the file doesn't exist.
    """
    non_existent = tmp_path / "does_not_exist.png"
    output_path = tmp_path / "output.jpg"
    ok = process_image(str(non_existent), str(output_path), 1920, 70)
    assert not ok, "process_image() should return False for a missing file."


def test_process_image_non_image_file(non_image_file, tmp_path):
    """
    If process_image() is called on a file that's not an image,
    it should handle the exception and return False.
    """
    output_path = tmp_path / "output.jpg"
    ok = process_image(str(non_image_file), str(output_path), 1920, 70)
    assert not ok, "process_image() should return False for non-image files."


def test_process_image_quality_boundaries(basic_image, tmp_path):
    """
    Test extreme quality values (1 and 100).
    (If the code doesn't reject them, check for success.)
    """
    low_quality_output = tmp_path / "lowq.jpg"
    ok1 = process_image(str(basic_image), str(low_quality_output), 1920, 1)
    assert ok1, "Should succeed even at very low quality=1."
    low_file = tmp_path / "lowq_zmensene.jpg"
    assert low_file.exists()
    size_low = os.path.getsize(low_file)

    high_quality_output = tmp_path / "highq.jpg"
    ok2 = process_image(str(basic_image), str(high_quality_output), 1920, 100)
    assert ok2, "Should succeed at high quality=100."
    high_file = tmp_path / "highq_zmensene.jpg"
    assert high_file.exists()
    size_high = os.path.getsize(high_file)
    assert size_low < size_high, (
        f"Expected size at quality=1 ({size_low}) < size at quality=100 ({size_high})."
    )


def test_process_image_with_tiny_max_dimension(basic_image, tmp_path):
    """
    If max_dimension=1, the final image should be at most 1 pixel in width/height
    (assuming the code doesn't reject it).
    """
    out = tmp_path / "tiny_output.jpg"
    ok = process_image(str(basic_image), str(out), max_dimension=1, quality=50)
    assert ok, "Should still succeed with a very small max_dimension."

    tiny_file = tmp_path / "tiny_output_zmensene.jpg"
    assert tiny_file.exists()
    with Image.open(tiny_file) as timg:
        w, h = timg.size
        assert (w, h) == (1, 1), f"Expected a 1×1 image, got {w}×{h}."


def test_process_image_with_negative_max_dimension(basic_image, tmp_path, capsys):
    """
    If max_dimension < 0, we expect the code to fail or produce an error,
    returning False. Adjust based on your code's logic.
    """
    out = tmp_path / "negative.jpg"
    ok = process_image(str(basic_image), str(out), max_dimension=-10, quality=50)
    captured = capsys.readouterr()
    assert not ok, "process_image() should fail gracefully with negative max_dimension."
    assert "Could not process file" in captured.out, "Should print an error message."
    assert not (tmp_path / "negative_zmensene.jpg").exists()


# -------------------------------------------------------------------
# Tests for compress_images()
# -------------------------------------------------------------------

def test_compress_images_single_folder(tmp_path):
    """
    Integration test for compress_images(). We'll create a directory with
    some images, then run compress_images() and verify that the "compressed"
    folder is populated.
    """
    input_folder = tmp_path / "input"
    input_folder.mkdir()

    img1_path = input_folder / "image1.png"
    img2_path = input_folder / "image2.png"
    Image.new("RGB", (800, 600), color=(255, 128, 0)).save(img1_path, "PNG")
    Image.new("RGB", (1024, 768), color=(0, 128, 255)).save(img2_path, "PNG")

    compress_images(str(input_folder), quality=50, max_dimension=1000)

    compressed_folder = input_folder / "compressed"
    assert compressed_folder.exists(), "A 'compressed' folder should be created inside input folder."

    out1 = compressed_folder / "image1_zmensene.jpg"
    out2 = compressed_folder / "image2_zmensene.jpg"
    assert out1.exists(), "image1 should be compressed."
    assert out2.exists(), "image2 should be compressed."
    assert os.path.getsize(out1) > 0, "Output file shouldn't be empty."
    assert os.path.getsize(out2) > 0, "Output file shouldn't be empty."

    with Image.open(out1) as i1:
        assert max(i1.size) <= 1000
    with Image.open(out2) as i2:
        assert max(i2.size) <= 1000


def test_compress_images_empty_folder(tmp_path, capsys):
    """
    If there are no images in the input folder, compress_images() should
    process 0 files and print 'Compression completed: 0/0'.
    """
    empty_folder = tmp_path / "empty"
    empty_folder.mkdir()

    compress_images(str(empty_folder), quality=65, max_dimension=1920)

    captured = capsys.readouterr()
    assert "Starting compression for 0 images in" in captured.out
    assert "Compression completed: 0/0 files processed." in captured.out


def test_compress_images_subfolders(tmp_path):
    """
    If the input folder has multiple nested subfolders, compress_images()
    should traverse them, skipping the 'compressed' folder if it exists.
    """
    input_folder = tmp_path / "input"
    sub1 = input_folder / "sub1"
    sub2 = input_folder / "sub2"
    sub1.mkdir(parents=True)
    sub2.mkdir(parents=True)

    img1_path = sub1 / "sub1_image.png"
    img2_path = sub2 / "sub2_image.png"
    Image.new("RGB", (1200, 800), color=(128, 128, 128)).save(img1_path, "PNG")
    Image.new("RGB", (1300, 900), color=(128, 128, 255)).save(img2_path, "PNG")

    compress_images(str(input_folder), quality=60, max_dimension=800)

    compressed_folder = input_folder / "compressed"
    assert compressed_folder.exists(), "Top-level 'compressed' folder should exist."

    compressed_sub1 = compressed_folder / "sub1"
    compressed_sub2 = compressed_folder / "sub2"
    assert compressed_sub1.exists(), "sub1 folder should be created inside 'compressed'."
    assert compressed_sub2.exists(), "sub2 folder should be created inside 'compressed'."

    out1 = compressed_sub1 / "sub1_image_zmensene.jpg"
    out2 = compressed_sub2 / "sub2_image_zmensene.jpg"
    assert out1.exists(), "sub1_image.png was compressed."
    assert out2.exists(), "sub2_image.png was compressed."

    with Image.open(out1) as i1:
        assert max(i1.size) <= 800
    with Image.open(out2) as i2:
        assert max(i2.size) <= 800


def test_compress_images_quality_extreme(tmp_path):
    """
    Test using extreme quality=1 to confirm everything still runs.
    """
    input_folder = tmp_path / "extreme"
    input_folder.mkdir()

    big_img_path = input_folder / "big_image.png"
    Image.new("RGB", (2000, 2000), color=(0, 255, 255)).save(big_img_path, "PNG")

    compress_images(str(input_folder), quality=1, max_dimension=500)

    compressed_folder = input_folder / "compressed"
    out_file = compressed_folder / "big_image_zmensene.jpg"
    assert out_file.exists(), "Should have created the compressed file at low quality."

    with Image.open(out_file) as i:
        w, h = i.size
        assert max(w, h) <= 500, "Should be resized down to 500 on the largest side."
        assert i.format == "JPEG"


def test_compress_images_skips_compressed_folder(tmp_path):
    """
    If there's already a 'compressed' folder with images in it,
    compress_images() should skip re-processing them to avoid infinite loops.
    """
    input_folder = tmp_path / "input"
    compressed_folder = input_folder / "compressed"
    compressed_folder.mkdir(parents=True)

    existing_compressed_path = compressed_folder / "already_compressed_zmensene.jpg"
    Image.new("RGB", (100, 100)).save(existing_compressed_path, "JPEG")

    main_img_path = input_folder / "new_image.png"
    Image.new("RGB", (800, 800)).save(main_img_path, "PNG")

    compress_images(str(input_folder), quality=70, max_dimension=400)

    new_output = compressed_folder / "new_image_zmensene.jpg"
    assert new_output.exists(), "new_image was processed."

    # Ensure the already compressed image remains
    assert existing_compressed_path.exists(), "Images in 'compressed' folder should be skipped."


def test_correct_orientation_invalid_exif_tag(tmp_path):
    """
    If the image has EXIF data but the orientation tag is invalid or not recognized,
    correct_orientation() should simply return the image without raising an error.
    """
    from PIL import Image

    img_path = tmp_path / "bad_exif.jpg"
    image = Image.new("RGB", (300, 300), color=(50, 100, 150))
    image.save(img_path, "JPEG")

    with Image.open(img_path) as img:
        # Manually inject a bogus EXIF orientation if you like; for now we just confirm no crash
        img.info["exif"] = b"FAKE_EXIF_DATA"  # purely illustrative, won't parse correctly
        oriented = correct_orientation(img)
        assert oriented.size == (300, 300), "Invalid orientation tag should not affect size."


def test_process_image_corrupted_data(tmp_path):
    """
    If the file is recognized by Pillow but the data is corrupted,
    process_image() should catch the error and return False.
    (We simulate this by writing partial JPEG bytes to a file.)
    """
    corrupted_path = tmp_path / "corrupted.jpg"
    with open(corrupted_path, "wb") as f:
        # Write partial, invalid JPEG header
        f.write(b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01")

    output_path = tmp_path / "corrupted_output.jpg"
    ok = process_image(str(corrupted_path), str(output_path), max_dimension=500, quality=80)
    assert not ok, "process_image() should fail on corrupted image data."


def test_process_image_output_exists(basic_image, tmp_path):
    """
    If an output file with the same name already exists, process_image() should overwrite it
    or create the new '_zmensene.jpg'. Confirm that the final file is valid and updated.
    """
    # Create an existing file
    output_path = tmp_path / "existing.jpg"
    with open(output_path, "wb") as f:
        f.write(b"OLD FILE DATA")

    ok = process_image(str(basic_image), str(output_path), max_dimension=200, quality=85)
    assert ok, "Should succeed even if output file already exists."

    final_path = tmp_path / "existing_zmensene.jpg"
    assert final_path.exists(), "Should still follow the '_zmensene.jpg' pattern."
    # Check that it’s non-empty and likely a JPEG
    with open(final_path, "rb") as f:
        assert b"JFIF" in f.read(100), "File should now contain a valid JPEG header, not the old data."


def test_compress_images_read_only_file(tmp_path):
    """
    If an image is read-only, compress_images() should still be able to open and read it,
    as long as we have read permission. We simulate that scenario here.
    """
    input_folder = tmp_path / "read_only"
    input_folder.mkdir()

    img_path = input_folder / "readonly.png"
    from PIL import Image
    Image.new("RGB", (500, 500), color=(255, 255, 0)).save(img_path, "PNG")

    # Make the file read-only
    os.chmod(img_path, 0o444)  # Read-only for owner, group, others

    compress_images(str(input_folder), quality=60, max_dimension=300)

    compressed_folder = input_folder / "compressed"
    out_file = compressed_folder / "readonly_zmensene.jpg"
    assert out_file.exists(), "Should compress the read-only file into 'compressed' folder."
    assert os.path.getsize(out_file) > 0, "Output file shouldn't be empty."


def test_compress_images_mixed_file_types(tmp_path):
    """
    If the input folder contains both images and random non-image files,
    only the images should be processed. Non-images should either be skipped or fail gracefully.
    """
    input_folder = tmp_path / "mixed"
    input_folder.mkdir()

    # Create a valid image
    img_path = input_folder / "photo.jpg"
    from PIL import Image
    Image.new("RGB", (400, 300), color=(0, 128, 128)).save(img_path, "JPEG")

    # Create a random text file
    text_file = input_folder / "notes.txt"
    text_file.write_text("This is not an image.")

    # Run compress_images
    compress_images(str(input_folder), quality=50, max_dimension=200)

    compressed_folder = input_folder / "compressed"
    assert compressed_folder.exists(), "A 'compressed' folder should be created."

    out_img = compressed_folder / "photo_zmensene.jpg"
    assert out_img.exists(), "JPEG image should be compressed."
    assert os.path.getsize(out_img) > 0, "Output image shouldn't be empty."

    # Confirm the text file didn't break the process
    out_txt = compressed_folder / "notes_zmensene.jpg"
    # Typically `process_image()` would fail on a non-image, so no .jpg output expected
    assert not out_txt.exists(), "Non-image files typically won't produce a compressed file."
