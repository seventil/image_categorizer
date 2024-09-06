import os

from kivy.logger import Logger
from PIL import Image

IMAGE_FILE_FORMATS = ["jpg", "jpeg", "png", "webp"]
DEFAULT_FILE_FORMAT = "jpeg"
DEFAULT_OUTPUT = "outputs"
DEFAULT_DATABANK_DIR = "databank"
DEFAULT_DB_PATH = os.path.join(DEFAULT_OUTPUT, DEFAULT_DATABANK_DIR)
MAX_SIZE = 1600
SCAN_DEFAULT_PATH = "inputs"


def filter_files(files: list[str], filters: str | list[str]) -> list[str]:
    """Filters files with wanted formats from the list of files."""
    if isinstance(filters, str):
        filters = [filters]
    filtered_files = []
    for file in files:
        if file.split(".")[-1].lower() in filters:
            filtered_files.append(file)

    return filtered_files


def scan_images_input(path: str = SCAN_DEFAULT_PATH) -> list[str]:
    """Scans input path and creates a list of images present within input path."""
    images = []
    content = {}
    for root, _, files in os.walk(path):
        content[root] = filter_files(files, IMAGE_FILE_FORMATS)

    for directory, files in content.items():
        for file in files:
            images.append(os.path.normcase(os.path.join(directory, file)))
    return images


def transfer_image(file: str, new_file_path: str, resize: bool):
    """Transfers the physical location of an image while optionally resizing it.
    Changes storage format to jpeg.
    """
    with Image.open(file).convert("RGB") as img:
        height = img.size[0]
        width = img.size[1]
        wpercent = MAX_SIZE / float(max(img.size))

        if wpercent < 1 and resize:
            hsize = int((height * float(wpercent)))
            wsize = int((width * float(wpercent)))
            img = img.resize((hsize, wsize))

        img.save(new_file_path, DEFAULT_FILE_FORMAT)

    Logger.debug(f"{file} was moved to {new_file_path}")
    if file != new_file_path:
        os.remove(file)
    return new_file_path


def full_path_from_relative(file: str, new_relative_path: str, suffix: str = "") -> str:
    base_name = os.path.basename(file)
    new_file_name = "".join((os.path.splitext(base_name)[0], suffix, f".{DEFAULT_FILE_FORMAT}"))
    new_file_path = os.path.normcase(
        os.path.join(new_relative_path, new_file_name)
    )
    return new_file_path
