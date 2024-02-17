import os

from image_nodes import IMAGE_FILE_FORMATS

SCAN_DEFAULT_PATH = "inputs"


def filter_files(
    files: list[str], filters: str | list[str]
) -> list[str]:
    """Filters files with wanted formats from the list of files."""
    if isinstance(filters, str):
        filters = [filters]
    filtered_files = []
    for file in files:
        if file.split(".")[-1].lower() in filters:
            filtered_files.append(file)

    return filtered_files


def scan_images_input(path: str = SCAN_DEFAULT_PATH) -> list:
    """Scans input path and creates a list of images present within input path."""
    images = []
    content = {}
    for root, _, files in os.walk(path):
        content[root] = filter_files(files, IMAGE_FILE_FORMATS)

    for directory, files in content.items():
        for file in files:
            images.append(os.path.join(directory, file))
    return images
