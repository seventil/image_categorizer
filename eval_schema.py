import json

from kivy.properties import ObjectProperty
from kivy.uix.checkbox import CheckBox

from databank_schema import DataBankSchema

DEFAULT_SCHEMA_PATH = "schema.json"


class LabeledCheckBox(CheckBox):
    def __init__(self, **kwargs):
        super(LabeledCheckBox, self).__init__(**kwargs)

    label = ObjectProperty(None, allownone=True)


type Mark = int
type Eval_Category = str
type Categories = list[Eval_Category]
type Evaluations = dict[Eval_Category, Mark]
type MarkedCheckBox = dict[Mark, LabeledCheckBox]
type CategorizedMarkedCheckBox = dict[Eval_Category, MarkedCheckBox]
type PrioritizedCategories = tuple[Eval_Category, ...] 


class EvaluationSchema:
    def __init__(self, path: str = DEFAULT_SCHEMA_PATH):
        with open(path, "r", encoding="utf-8") as fstream:
            json_schema: dict[str, list[str]] = json.load(fstream)

        self.__pr_categories: PrioritizedCategories = tuple(
            json_schema[DataBankSchema.categories]
        )
        self.__total_evals: Categories = [
            cat for cats in json_schema.values() for cat in cats
        ]
        self._eval_category_check_boxes: CategorizedMarkedCheckBox = {
            eval_category: {} for eval_category in self.__total_evals
        }

    @property
    def total_evals(self) -> Categories:
        return self.__total_evals

    @property
    def prioritized_categories(self) -> PrioritizedCategories:
        return self.__pr_categories

    def get_checks(self, eval_category: str) -> MarkedCheckBox:
        return self._eval_category_check_boxes.get(eval_category, {})

    def assign_checks(self, eval_category: str, mark: Mark, check_box: CheckBox) -> None:
        self._eval_category_check_boxes[eval_category][mark] = check_box

    def reload_evaluations(self, current_evals: Evaluations) -> None:
        for eval_category in self.__total_evals:
            eval_checkboxes = self.get_checks(eval_category)
            for checkbox in eval_checkboxes.values():
                checkbox.active = False

            current_mark = current_evals.get(eval_category)
            if current_mark is not None:
                eval_checkboxes[current_mark].active = True

    def reset_current_evals(self) -> None:
            for eval_category in self.__total_evals:
                eval_checkboxes = self.get_checks(eval_category)
                for checkbox in eval_checkboxes.values():
                    checkbox.active = False
