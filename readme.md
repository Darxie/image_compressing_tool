# Image Compression and Orientation Correction GUI

This Python script provides a **GUI-based tool** for compressing images in a specified folder and its subfolders, maintaining their aspect ratio while resizing them. It also **corrects image orientation** based on EXIF metadata if available. The processed images are saved as high-quality JPEG files in an output folder named `compressed`.

## Features

- ✅ **Graphical User Interface (GUI)** for ease of use.
- ✅ **Automatically corrects image orientation** based on EXIF data.
- ✅ **Resizes images** to a maximum dimension while maintaining the original aspect ratio.
- ✅ **Compresses images** to JPEG format with a specified quality level.
- ✅ **Uses multi-threading** to process images concurrently for faster performance.
- ✅ **Processes images in subfolders** and maintains the directory structure.
- ✅ **Skips already processed images** by checking for the output folder.

## Requirements

- Python 3.x
- `Pillow` library for image processing
- `concurrent.futures` for multi-threading

## Installation

To install the required dependencies, run:

```sh
pip install pillow
```

## Usage

### Running the Application

1. Run the script:
   ```sh
   python image_compressor.py
   ```
2. Use the **GUI** to:
   - Select the **input folder**.
   - Set **quality level** (1-100).
   - Set **maximum dimension** (default: 1920 pixels).
   - Click **Start Compression** to process images.

### Output Folder

- Processed images are saved in a **compressed** subfolder inside the selected input folder.
- The script maintains the directory structure for easy organization.
- Original files remain untouched.

### EXIF Orientation Fix

- If images have **EXIF orientation data**, the script will **automatically rotate** them for correct display.

## Example Output

```sh
Starting compression for 100 images in 'path/to/images'...
[1/100] Processed an image
[2/100] Processed an image
...
Compression completed: 100/100 files processed.
```

## Code Overview

- `correct_orientation(img)`: **Fixes EXIF rotation** for images.
- `process_image(img_path, output_path, max_dimension, quality)`: **Resizes and compresses** an image.
- `compress_images(input_folder, quality, max_dimension)`: **Processes all images** inside the input folder using multi-threading.
- **GUI Components:** Built using **Tkinter** for easy file selection and settings adjustment.

## Contributing

If you'd like to contribute to the script, feel free to fork this repository, submit issues, or open pull requests with improvements.

## License

This script is open-source and free to use. Modify and redistribute as per your needs.

---

🚀 **Enjoy fast and efficient image compression with a simple GUI!**

