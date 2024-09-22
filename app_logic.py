from kivy import Logger

from databank import JSONDataBank
from file_utils import scan_images_input
from image_nodes import EvaluatedPic, ImageNodesHolder, NodePics

DEFAULT_EVAL_RANGE = 2


class OnScreenImageHandler:
    """Manager class that keeps information on the current image (where the cursor
    is at) and also moves the cursor."""

    def __init__(self, input_path: str, nodes_holder: ImageNodesHolder | None = None):
        """Validate images in holder and physically stored images."""
        physical_images: list[str] = scan_images_input(input_path)
        self.cursor = ListCursor(len(physical_images))

        if nodes_holder is not None:
            self._nodes_holder = nodes_holder
            self.__images: list[EvaluatedPic] = []
            self.scan_images(physical_images)
            self.scan_mode_append = False
        else:
            self._nodes_holder = ImageNodesHolder()
            self.__images: list[EvaluatedPic] = [
                EvaluatedPic(path) for path in physical_images
            ]
            self.scan_mode_append = True

        self.__assign_current()

    def next(self) -> None:
        self.cursor.shift(1)
        self.__assign_current()

    def previous(self) -> None:
        self.cursor.shift(-1)
        self.__assign_current()

    def save_current(self) -> None:
        self._nodes_holder.post_pic(self.current)

    def save_eval_data(self) -> None:
        JSONDataBank.save(self._nodes_holder, append=self.scan_mode_append)

    @property
    def empty(self) -> bool:
        return len(self.__images) == 0

    def scan_images(self, physical_images):
        nodes_images: NodePics = self._nodes_holder.list_images()
        for node_pic in nodes_images:
            if node_pic.storage_path not in physical_images:
                Logger.warning(f"{node_pic.storage_path} from databank does not exist, deleting")
                node_pic.node_ref.pop_image(node_pic)
            else:
                Logger.debug(f"Added {node_pic.storage_path} to onscreen images handler")
                self.__images.append(node_pic)

        node_img_paths = [img.storage_path for img in nodes_images]
        for pth in physical_images:
            if pth not in node_img_paths:
                Logger.warning("found physical image, not present in databank")
                pic = EvaluatedPic(pth)
                Logger.debug(f"Added {pic} to onscreen images handler")
                self.__images.append(pic)
                self._nodes_holder.post_pic(pic)

    def __assign_current(self) -> None:
        if self.empty:
            return
        self.current = self.__images[int(self.cursor)]


class ListCursor:
    """Cursor that allows to move within selected length."""

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.counter: int = 0

    def shift(self, amount: int) -> None:
        self.counter += amount
        self.counter = self.counter % self.limit

    def __int__(self) -> int:
        return self.counter
