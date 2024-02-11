import os

from image_nodes import IMAGE_FILE_FORMATS, EvaluatedPic

SCAN_DEFAULT_PATH = "inputs"
DEFAULT_EVAL_RANGE = 2


def filter_files(
    files: list[str], filters: str | list[str]
) -> list[str]:
    """Filters files with wanted formats from the list of files.

    Args:
        files (List[str]): files with different formats.
        filters (str | List[str]): names of formats to be in returned list.
    Returns:
        List[str] of files with filtered formats.
    """
    if isinstance(filters, str):
        filters = [filters]
    filtered_files = []
    for file in files:
        if file.split(".")[-1].lower() in filters:
            filtered_files.append(file)

    return filtered_files


def scan_images_input(path: str = SCAN_DEFAULT_PATH) -> list:
    images = []
    content = {}
    for root, _, files in os.walk(path):
        content[root] = filter_files(files, IMAGE_FILE_FORMATS)

    for directory, files in content.items():
        for file in files:
            images.append(os.path.join(directory, file))
    return images


class OnScreenImageHandler:
    def __init__(self, user_input_path: str):
        self.__images: list[str | EvaluatedPic] = scan_images_input(user_input_path)
        self.cursor = ListCursor(len(self.__images))
        self.__current = None
        self.__assign_current()

    def next(self) -> None:
        self.cursor >> 1
        self.__assign_current()

    def previous(self) -> None:
        self.cursor << 1
        self.__assign_current()

    @property
    def current(self) -> EvaluatedPic | None:
        return self.__current
    
    @property
    def empty(self) -> bool:
        return len(self.__images) == 0

    def __assign_current(self) -> None:
        if self.empty:
            return
        new_image = self.__images[int(self.cursor)]
        if not isinstance(new_image, EvaluatedPic):
            self.__current = EvaluatedPic(new_image)
            self.__images[int(self.cursor)] = self.__current
        else:
            self.__current = new_image


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





