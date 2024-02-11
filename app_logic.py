import json
import os

from kivy.uix.checkbox import CheckBox

from image_nodes import (IMAGE_FILE_FORMATS, DataBank, DataBankSchema,
                         EvaluatedPic)

SCAN_DEFAULT_PATH = "inputs"
DEFAULT_SCHEMA_PATH = "schema.json"
DEFAULT_EVAL_RANGE = 2


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


def scan_images_input(path: str = SCAN_DEFAULT_PATH) -> list:
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


class EvaluationSchema:
    def __init__(self, path: str = DEFAULT_SCHEMA_PATH):
        with open(path, "r", encoding="utf-8") as fstream:
            json_schema: dict[str, list[str]] = json.load(fstream)
        self.__priority_categories = tuple(json_schema[DataBankSchema.categories])
        self.__total_evals = [cat for cats in json_schema.values() for cat in cats]
        self._eval_category_check_boxes: dict[str, dict[int, CheckBox]] = {
            eval_category: {} for eval_category in self.__total_evals
        }

    @property
    def total_evals(self) -> list[str]:
        return self.__total_evals

    @property
    def priority_categories(self) -> tuple[str, ...]:
        return self.__priority_categories

    def get_checks(self, eval_category: str) -> dict[int, CheckBox]:
        return self._eval_category_check_boxes.get(eval_category, {})

    def assign_checks(self, eval_category: str, mark: int, check_box: CheckBox) -> None:
        self._eval_category_check_boxes[eval_category][mark] = check_box


def read_schema(path: str = DEFAULT_SCHEMA_PATH) -> dict[str, list[str]]:
    with open(path, "r", encoding="utf-8") as fstream:
        json_schema = json.load(fstream)
    return json_schema
