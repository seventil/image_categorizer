import json
import os

from kivy.uix.checkbox import CheckBox

from image_nodes import IMAGE_FILE_FORMATS, DataBank, DataBankSchema

SCAN_DEFAULT_PATH = "inputs"
DEFAULT_SCHEMA_PATH = "schema.json"
DEFAULT_EVAL_RANGE = 2


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
