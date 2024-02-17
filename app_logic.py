import os

from databank import JSONDataBank
from file_utils import scan_images_input
from image_nodes import EvaluatedPic, ImageNodesHolder

DEFAULT_EVAL_RANGE = 2


class OnScreenImageHandler:
    """Manager class that keeps information on the current image (where the cursor
    is at) and also moves the cursor."""
    def __init__(self, user_input_path: str, nodes_holder: ImageNodesHolder | None = None):
        self.__images: list[str | EvaluatedPic] = scan_images_input(user_input_path)
        self.cursor = ListCursor(len(self.__images))
        self.current = None
        if nodes_holder is not None:
            self._nodes_holder = nodes_holder
        else:
            self._nodes_holder = ImageNodesHolder()

        self.__assign_current()

    def next(self) -> None:
        self.cursor >> 1
        self.__assign_current()

    def previous(self) -> None:
        self.cursor << 1
        self.__assign_current()

    def save_current(self) -> None:
        self._nodes_holder.post_pic(self.current)

    def save_eval_data(self) -> None:
        JSONDataBank.save(self._nodes_holder)
    
    @property
    def empty(self) -> bool:
        return len(self.__images) == 0

    def __assign_current(self) -> None:
        if self.empty:
            return
        new_image = self.__images[int(self.cursor)]
        if not isinstance(new_image, EvaluatedPic):
            self.current = EvaluatedPic(new_image)
            self.__images[int(self.cursor)] = self.current
        else:
            self.current = new_image


class ListCursor:
    """Cursor that allows to move within selected length."""
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
