import json
import os
from typing import Dict, List, Tuple

DEFAULT_PATH = "databank"
DEFAULT_ENCODING = "utf-8"
JSON_INDENT = 4
MAX_ITEMS_PER_NODE = 1000
STORAGE_FORMAT = "json"


class DataBankSchema:
    """Describes the names of json nodes for image info"""

    storage_path = "Path"
    categories = "Categories"
    evals = "Evals"


class EvaluatedPic:
    """Encapsulates evaluations for an image with info on where it is stored.

    Attributes:
        storage_path (str): describes where the image is storred.
        categories (List[str]): categories (from schema) that the image fits.
        evals (Dict[str, int]): evaluations that where set for the image.
        resize (bool): if the image should be resized to save storage space.
            Defaults to True. Should be set to False if high-definition texture
            is important.
    """

    def __init__(
        self,
        storage_path: str,
        categories: List[str] = None,
        evals: Dict[str, int] = None,
        resize: bool = True,
    ) -> None:
        """Initialize the object with all attributes.

        Args:
            storage_path (str): describes where the image is storred.
            categories (List[str]): categories (from schema) that the image fits.
            evals (Dict[str, int]): evaluations that where set for the image.
            resize (bool): if the image should be resized to save storage space.
                Defaults to True. Should be set to False if high-definition texture
                is important.
        """
        self.storage_path = storage_path
        if categories is None:
            self.categories = []
        else:
            self.categories = categories
        if evals is None:
            self.evals = {}
        else:
            self.evals = evals
        self.resize = resize

    def add_category(self, category: str, category_priority: Tuple[str]) -> None:
        """Add a category that the image fits into.

        Args:
            category (str): name of the category from the schema file.
            category_priority (Tuple[str]): sorted categories from schema, where
                lowest index indicates higher folder (closer to root) in the databank
                structure.
        """
        if category not in self.categories:
            self.categories.append(category)
            self.__sort_categories(category_priority)

    def __sort_categories(self, category_priority: Tuple[str]) -> None:
        """Sort categories according to schema priorities.

        Args:
            category_priority (Tuple[str]): sorted categories from schema, where
                lowest index indicates higher folder (closer to root) in the databank
                structure.
        """
        image_cat_idx = 0
        for cat in category_priority:
            if cat in self.categories:
                cur_idx = self.categories.index(cat)
                self.categories[cur_idx] = self.categories[image_cat_idx]
                self.categories[image_cat_idx] = cat
                image_cat_idx += 1

    def evaluate(self, category: str, mark: int) -> None:
        """Add or change an evaluation for the image.

        Args:
            category (str): name of the eval from the schema file.
            mark (int): relative evaluation mark for the image in the specified
                category.
        """
        self.evals[category] = mark


class ImageStorageNode:
    """A node to store evaluated image objects differentiated by categories.

    Attributes:
        ranks (Tuple[int] | None): category mark of the images contained in the node.
        bucket (str | None): bucket that splits the images by MAX_ITEMS_PER_NODE.
        name (str | None): name of the node, containing info on it's ranks for
            categories and subcategories and its bucket.
        images (List[EvaluatedPic]): evaluated images.
    """

    def __init__(
        self,
        name: str | None = None,
        ranks: Tuple[int] | None = None,
        bucket: str | None = None,
        evaluated_pics: List[dict] | None = None,
    ) -> None:
        """Instantiate the node with possible rank and json data for pics.

        Args:
            name (str | None): name of the node.
            ranks (Tuple[int] | None): category mark of the images contained in the node.
            bucket (str | None): bucket that splits the images by MAX_ITEMS_PER_NODE.
            evaluated_pics (List[dict] | None): json data for pics. Defaults to None.
        """
        if name is not None:
            self.__name: str = name
            name = name.split("_")
            self.bucket: str = name.pop(-1)
            self.ranks: Tuple[int] = tuple(map(int, name))
        if ranks is not None:
            self.ranks = ranks
        if bucket is not None:
            self.bucket = bucket

        if evaluated_pics is None:
            self.images: List[EvaluatedPic] = []
        else:
            self.images: List[EvaluatedPic] = [
                EvaluatedPic(
                    storage_path=pic.get(DataBankSchema.storage_path),
                    categories=pic.get(DataBankSchema.categories),
                    evals=pic.get(DataBankSchema.evals),
                )
                for pic in evaluated_pics
            ]

    @property
    def name(self) -> str:
        """The node name property.

        Contains info on it's ranks for categories and subcategories and its bucket.
        """
        if not self.__name:
            name = [rank for rank in self.ranks]
            name.append(self.bucket)
            self.__name = "_".join(name)
        return self.__name

    def add_image(self, image: EvaluatedPic) -> bool:
        """Add image object to the node.

        Args:
            image (EvaluatedPic): image to add.
        Returns:
            bool: if the image was added.
        """
        if len(self.images > MAX_ITEMS_PER_NODE):
            return False
        self.images.append(image)
        return True

    def pop_image(self) -> EvaluatedPic:
        """Pop image from the node."""
        return self.images.pop()


class ImageNodesHolder:
    """Parent for image nodes that maps nodes to their respective categories.

    Attributes:
        image_nodes (Dict[str, List[ImageStorageNode]]): mapping of nodes to categories.
    """

    def __init__(self, image_nodes: Dict[str, List[ImageStorageNode]]) -> None:
        """Initialize node container.

        Args:
            image_nodes (Dict[str, ImageStorageNode]): mapping of image nodes
                with their categories in hierarchy notation.
        """
        self.__image_nodes = image_nodes

    @property
    def image_nodes(self):
        """Image nodes property.

        Returns:
            Dict[str, List[ImageStorageNode]] mapping of image nodes with their
                categories in hierarchy notation.
        """
        return self.__image_nodes

    def post_pic(self, image: EvaluatedPic) -> None:
        """Fits the image object based on its attributes.

        Takes into account primary category, all present subcategories and their
        respective evaluations. If several nodes match the criteria, finds the
        one that has empty space for the image. If a fitting node does not exist,
        creates it.

        Asserts categories of the EvaluatedPic are sorted as per the schema.
        Asserts that the image is not present in the nodes, otherwise creates
            a duplicate.

        Args:
            image (EvaluatedPic): image the node is searched for.
        """
        relative_path = os.path.join(image.categories)
        sibling_nodes = self.__image_nodes.get(relative_path)
        fitting_mark_nodes = [
            node
            for node in sibling_nodes
            if node.ranks == (image.evals[rank] for rank in image.categories)
        ]
        for node in fitting_mark_nodes:
            if node.add_image(image):
                return


class DataBank:
    """Responsible for saving evaluated image info to a physical storage in JSON."""

    @staticmethod
    def filter_files(files: List[str], filters: str | List[str]) -> List[str]:
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
            if file.split(".")[-1].lower() == STORAGE_FORMAT:
                filtered_files.append(file)

        return filtered_files

    @classmethod
    def read(cls, path: str = DEFAULT_PATH) -> ImageNodesHolder:
        """Read the databank folder.

        The root must contain folder structure fitting categories and json files
        with lists of evaluated images data.

        Args:
            path (str): path to the root folder. Defaults to DEFAULT_PATH.
        """
        image_nodes = {}
        for folder, _, files in os.walk(path):
            if len(files) == 0:
                continue
            rel_path = os.path.relpath(folder, start=path)
            files = cls.filter_files(files, STORAGE_FORMAT)

            nodes = []
            for file in files:
                full_path = os.path.join(folder, file)
                with open(full_path, "r", encoding=DEFAULT_ENCODING) as fstream:
                    eval_pics_json_data = json.load(fstream)
                node_name = os.path.basename(full_path).split(".")[0]

                nodes.append(
                    ImageStorageNode(
                        name=node_name,
                        evaluated_pics=eval_pics_json_data,
                    )
                )
            image_nodes[rel_path] = nodes
        return ImageNodesHolder(image_nodes)

    @staticmethod
    def save(
        nodes_holder: ImageNodesHolder,
        root_path: str = DEFAULT_PATH,
    ):
        """Save node structure to the databank folder.

        The root contains folder structure fitting categories and json files
        with lists of evaluated images data.

        Args:
            nodes_holder (ImageNodesHolder): nodes structure to save.
            root_path (str): path to the root folder. Defaults to DEFAULT_PATH.
        """
        for path, image_nodes in nodes_holder.image_nodes.items():
            for node in image_nodes:
                evaluated_images = []
                for img in node.images:
                    evaluated_img_json = {
                        DataBankSchema.storage_path: img.storage_path,
                        DataBankSchema.categories: img.categories,
                        DataBankSchema.evals: img.evals,
                    }
                    evaluated_images.append(evaluated_img_json)
                output_name = f"{node.name}.{STORAGE_FORMAT}"
                output_path = os.path.join(root_path, path)
                os.makedirs(output_path, exist_ok=True)
                with open(
                    os.path.join(output_path, output_name),
                    "w",
                    encoding=DEFAULT_ENCODING,
                ) as fstream:
                    json.dump(evaluated_images, fstream, indent=JSON_INDENT)
