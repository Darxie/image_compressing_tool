# Image Compression and Orientation Correction Script

This Python script compresses images in a specified folder and its subfolders, maintaining their aspect ratio while resizing them. It also corrects the image orientation based on the EXIF data if available. The processed images are saved as high-quality JPEG files in an output folder named `compressed`.

## Features

- Automatically corrects image orientation based on EXIF data.
- Resizes images to a maximum dimension while maintaining the original aspect ratio.
- Compresses images to JPEG format with a specified quality level.
- Uses multi-threading to process images concurrently for faster performance.
- Processes images in subfolders and maintains the directory structure.
- Skips already processed images by checking for the output folder.

## Requirements

- Python 3.x
- `Pillow` library for image processing
- `concurrent.futures` for multi-threading

### Install Dependencies

To install the required dependencies, use the following command:

pip install pillow

## Usage

### 1. Running the Script with an Input Folder

You can specify the folder containing the images to be processed by providing it as an argument when running the script. For example:

python compress_images.py "path/to/images"

If no input folder is provided, the script will attempt to use a default folder path (which can be specified in the code).

### 2. Parameters

- **quality**: (optional) JPEG quality for compression. Default is 65. It is a value between 0 (worst) and 100 (best).
- **max_dimension**: (optional) Maximum width or height for resizing images. Default is 1920. Images are resized proportionally based on this dimension.

Example with custom quality and max dimension:

python compress_images.py "path/to/images" 80 1600

### 3. Output Folder

Processed images are saved in a subfolder named `compressed` within the input folder. The script maintains the directory structure, so images from subfolders are saved in corresponding subfolders inside `compressed`.

### 4. EXIF Orientation Fix

If images have EXIF orientation data (common in photos taken with smartphones), the script will automatically rotate the images based on this data to ensure they are correctly oriented.

## Example Output

Starting compression for 100 images in 'path/to/images'...
[1/100] Processed an image
[2/100] Processed an image ...
Compression completed: 100/100 files processed.

## Code Overview

- **correct_orientation(img)**: Corrects the orientation of an image based on EXIF data.
- **process_image(img_path, output_path, max_dimension, quality)**: Processes and compresses a single image, correcting orientation, resizing it, and saving it in JPEG format with the specified quality.
- **compress_images(input_folder, quality=65, max_dimension=1920)**: Main function that traverses the input folder and processes all images. It uses multi-threading for parallel processing.

## Contributing

If you'd like to contribute to the script, feel free to fork this repository, submit issues, or open pull requests with improvements.

## License

This script is open-source and free to use. Modify and redistribute as per your needs.
