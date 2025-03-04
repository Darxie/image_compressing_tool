import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
from concurrent.futures import ThreadPoolExecutor


def correct_orientation(img):
    try:
        exif = img._getexif()
        if exif is not None:
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
        return img


def process_image(img_path, output_path, max_dimension, quality):
    try:
        with Image.open(img_path) as img:
            img = correct_orientation(img)
            img = img.convert("RGB")
            base_name, _ = os.path.splitext(output_path)
            output_path = base_name + "_zmensene.jpg"
            width, height = img.size

            if width > height:
                new_width = min(width, max_dimension)
                new_height = int((new_width / width) * height)
            else:
                new_height = min(height, max_dimension)
                new_width = int((new_height / height) * width)

            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            img.save(output_path, "JPEG", quality=quality, optimize=True, progressive=True)
            return True
    except Exception as e:
        print(f"Error processing {img_path}: {e}")
        return False


def compress_images(input_folder, quality=65, max_dimension=1920, progress_callback=None):
    output_folder = os.path.join(input_folder, "compressed")
    total_files = sum(len(files) for _, _, files in os.walk(input_folder) if output_folder not in _)
    if total_files == 0:
        print(f"Compression completed: 0/0 files processed.")
        return
    processed_files = 0

    with ThreadPoolExecutor() as executor:
        futures = []
        for root, _, files in os.walk(input_folder):
            if output_folder in root:
                continue
            relative_path = os.path.relpath(root, input_folder)
            output_dir = os.path.join(output_folder, relative_path)
            os.makedirs(output_dir, exist_ok=True)

            for file in files:
                img_path = os.path.join(root, file)
                out_path = os.path.join(output_dir, file)
                if os.path.isfile(img_path):
                    futures.append(executor.submit(process_image, img_path, out_path, max_dimension, quality))

        for future in futures:
            if future.result():
                processed_files += 1
                if progress_callback:
                    progress_callback(processed_files, total_files)

    return processed_files, total_files


def start_compression():
    input_folder = folder_var.get()
    quality = int(quality_var.get())
    max_dimension = int(dim_var.get())

    if not input_folder:
        messagebox.showerror("Error", "Please select an input folder.")
        return

    progress_label.config(text="Processing...")

    def update_progress(processed, total):
        progress_label.config(text=f"Processed {processed}/{total} images")

    def run():
        processed, total = compress_images(input_folder, quality, max_dimension, update_progress)
        progress_label.config(text=f"Compression completed: {processed}/{total} images processed.")

    threading.Thread(target=run, daemon=True).start()


def select_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        folder_var.set(folder_selected)

if __name__ == "__main__":
    # GUI Setup
    root = tk.Tk()
    root.title("Image Compressor")
    root.geometry("450x350")
    root.configure(bg="#f0f0f0")

    frame = tk.Frame(root, padx=10, pady=10, bg="#f0f0f0")
    frame.pack(expand=True)

    tk.Label(frame, text="Select Input Folder:", bg="#f0f0f0", font=("Arial", 12)).pack(pady=5)
    folder_var = tk.StringVar()
    folder_entry = tk.Entry(frame, textvariable=folder_var, width=40, font=("Arial", 10))
    folder_entry.pack(pady=5)
    tk.Button(frame, text="Browse", command=select_folder, font=("Arial", 10), bg="#4CAF50", fg="white").pack(pady=5)

    tk.Label(frame, text="Quality (1-100):", bg="#f0f0f0", font=("Arial", 12)).pack(pady=5)
    quality_var = tk.StringVar(value="65")
    tk.Entry(frame, textvariable=quality_var, width=10, font=("Arial", 10)).pack(pady=5)

    tk.Label(frame, text="Max Dimension:", bg="#f0f0f0", font=("Arial", 12)).pack(pady=5)
    dim_var = tk.StringVar(value="1920")
    tk.Entry(frame, textvariable=dim_var, width=10, font=("Arial", 10)).pack(pady=5)

    tk.Button(frame, text="Start Compression", command=start_compression, font=("Arial", 12), bg="#2196F3",
              fg="white").pack(pady=10)
    progress_label = tk.Label(frame, text="", bg="#f0f0f0", font=("Arial", 10))
    progress_label.pack(pady=10)

    root.mainloop()
