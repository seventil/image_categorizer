import json

from kivy.properties import ObjectProperty
from kivy.uix.checkbox import CheckBox

from databank_schema import DataBankSchema

DEFAULT_SCHEMA_PATH = "schema.json"


class LabeledCheckBox(CheckBox):
    """Checkbox ui element with a label (mark).
    Can be used to display with a text label.
    """
    def __init__(self, **kwargs):
        super(LabeledCheckBox, self).__init__(**kwargs)

    label = ObjectProperty(None, allownone=True)


type Mark = int
"""Relative evaluation mark for the image in the specified category."""

type Eval_Category = str
"""Name of the category from the schema file. Includes only "Category" from schema
and not any regular eval from schema."""

type Categories = list[Eval_Category]
"""Categories names (from schema) that the image fits or might fit."""

type Evaluations = dict[Eval_Category, Mark]
"""Mapping of evaluation categories to numerical marks."""

type MarkedCheckBox = dict[Mark, LabeledCheckBox]
"""Mapping of a numerical mark to corresponding ui checkbox element."""

type CategorizedMarkedCheckBox = dict[Eval_Category, MarkedCheckBox]
"""Mapping of a Evaluation category name with its marks and checkboxes."""

type PrioritizedCategories = tuple[Eval_Category, ...]
"""Sorted categories names from schema, where lowest index indicates higher folder 
(closer to root) in the databank structure."""


class EvaluationSchema:
    """Wrapper class for user-defined evaluation schema that also holds info
    on UI elements bound to the evluation schema components.
    """
    def __init__(self, path: str = DEFAULT_SCHEMA_PATH):
        """Initialize the object based on schema json file."""
        with open(path, "r", encoding="utf-8") as fstream:
            json_schema: dict[str, list[str]] = json.load(fstream)

        self.__pr_categories: PrioritizedCategories = tuple(
            json_schema[DataBankSchema.categories]
        )
        self.total_evals: list[Eval_Category] = [
            cat for cats in json_schema.values() for cat in cats
        ]
        self._eval_category_check_boxes: CategorizedMarkedCheckBox = {
            eval_category: {} for eval_category in self.total_evals
        }

    @property
    def prioritized_categories(self) -> PrioritizedCategories:
        """PrioritizedCategories"""
        return self.__pr_categories

    def get_checks(self, eval_category: Eval_Category) -> MarkedCheckBox:
        """Get MarkedCheckBox mapping for specified evaluation category name."""
        return self._eval_category_check_boxes.get(eval_category, {})

    def assign_checks(self, eval_category: Eval_Category, mark: Mark, check_box: LabeledCheckBox) -> None:
        """Create a link between evaluation category name, numerical evaluation mark and
        their corresponding checkbox item."""
        self._eval_category_check_boxes[eval_category][mark] = check_box

    def reload_evaluations(self, current_evals: Evaluations) -> None:
        """Given evaluations from the image, reload corresponding UI checkboxes."""
        for eval_category in self.total_evals:
            eval_checkboxes = self.get_checks(eval_category)
            for checkbox in eval_checkboxes.values():
                checkbox.active = False

            current_mark = current_evals.get(eval_category)
            if current_mark is not None:
                eval_checkboxes[current_mark].active = True

    def reset_current_evals(self) -> None:
        """Reset all UI checkboxes to the false state."""
        for eval_category in self.total_evals:
            eval_checkboxes = self.get_checks(eval_category)
            for checkbox in eval_checkboxes.values():
                checkbox.active = False
