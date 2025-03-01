import os
import sys
from PIL import Image
from concurrent.futures import ThreadPoolExecutor


def correct_orientation(img):
    """
    Rotate an image based on EXIF orientation (tag=274) if present.
    """
    try:
        exif = img._getexif()
        if exif is not None:
            # Look for orientation tag (274) in EXIF data
            orientation_tag = 274
            if orientation_tag in exif:
                value = exif[orientation_tag]
                if value == 3:
                    img = img.rotate(180, expand=True)
                elif value == 6:
                    img = img.rotate(270, expand=True)
                elif value == 8:
                    img = img.rotate(90, expand=True)
        return img
    except Exception:
        # If EXIF data is missing or cannot be read, just return the original image
        return img


def process_image(img_path, output_path, max_dimension, quality):
    """
    Open an image, optionally resize it, and save as JPEG with '_zmensene.jpg' suffix.
    Returns True on success, False on failure.
    """
    try:
        # Open the image and convert unsupported formats to JPEG
        with Image.open(img_path) as img:
            # Correct orientation based on EXIF data
            img = correct_orientation(img)

            # Convert all images to JPEG format to save space
            img = img.convert("RGB")

            # Append the suffix _zmensene to the file name
            base_name, _ = os.path.splitext(output_path)
            output_path = base_name + "_zmensene.jpg"

            # Calculate the new size, maintaining aspect ratio
            width, height = img.size

            if width > height:
                new_width = min(width, max_dimension)
                new_height = int((new_width / width) * height)
            else:
                new_height = min(height, max_dimension)
                new_width = int((new_height / height) * width)

            # If max_dimension is invalid (e.g. negative), resizing might fail
            if new_width <= 0 or new_height <= 0:
                raise ValueError("Invalid max_dimension resulted in non-positive target size.")

            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            img.save(output_path, "JPEG", quality=quality, optimize=True, progressive=True)
            return True

    except Exception as e:
        print(f"Could not process file '{img_path}': {e}")
        return False


def compress_images(input_folder, quality=65, max_dimension=1920):
    """
    Recursively compress all images in 'input_folder' into a 'compressed' subdirectory,
    preserving folder structure. Skips re-compressing images already in 'compressed' folder.
    """
    output_folder = os.path.join(input_folder, "compressed")

    total_files = sum(len(files) for _, _, files in os.walk(input_folder) if output_folder not in _)
    processed_files = 0

    print(f"Starting compression for {total_files} images in '{input_folder}'...")

    with ThreadPoolExecutor() as executor:
        futures = []

        for root, _, files in os.walk(input_folder):
            # Skip the output folder to avoid re-processing compressed images
            if output_folder in root:
                continue

            # Create corresponding directory in output_folder
            relative_path = os.path.relpath(root, input_folder)
            output_dir = os.path.join(output_folder, relative_path)
            os.makedirs(output_dir, exist_ok=True)

            for file in files:
                img_path = os.path.join(root, file)
                out_path = os.path.join(output_dir, file)

                if os.path.isfile(img_path):
                    futures.append(
                        executor.submit(
                            process_image, img_path, out_path, max_dimension, quality
                        )
                    )

        for future in futures:
            if future.result():
                processed_files += 1
                print(f"[{processed_files}/{total_files}] Processed an image")

    print(f"Compression completed: {processed_files}/{total_files} files processed.")


# Default input folder path (used if no command-line argument is provided)
default_input_folder = ''

# Check if an argument is provided for the input folder, otherwise use the default
input_folder = sys.argv[1] if len(sys.argv) > 1 else default_input_folder

compress_images(input_folder)
