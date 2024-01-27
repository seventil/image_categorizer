import os

from image_nodes import IMAGE_FILE_FORMATS, DataBank

SCAN_DEFAULT_PATH = "inputs"


def scan_images_input(path: str = SCAN_DEFAULT_PATH):
    images = []
    content = {}
    for root, _, files in os.walk(path):
        content[root] = DataBank.filter_files(files, IMAGE_FILE_FORMATS)

    for directory, files in content.items():
        for file in files:
            images.append(os.path.join(directory, file))
    return images


class ListCursor:
    def __init__(self, limit: int):
        self.limit = limit
        self.counter: int = 0
        
    def __rshift__(self, amount: int):
        self.counter += amount
        self.counter = self.counter % self.limit

    def __lshift__(self, amount: int):
        self.counter -= amount
        self.counter = self.counter % self.limit

    def __int__(self):
        return self.counter
