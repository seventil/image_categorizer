import os
from datetime import datetime

from eval_schema import (Categories, EvalCategory, Evaluations, Mark,
                         PrioritizedCategories)
from file_utils import DEFAULT_OUTPUT, full_path_from_relative, transfer_image

MAX_ITEMS_PER_NODE = 1000
DEFAULT_UNCATEGORIZED_OUTPUT = "uncategorized"


type CategoryHierarchyPath = str

type ImageStoragePath = str
"""Full path to the image. Consists of scan directory + Optional(CategoryHierarchyPath)
 + file name."""

type SiblingNodes = list[ImageStorageNode]
"""A list of nodes with the same assigned categories."""

type NodesCatsMap = dict[tuple[EvalCategory, ...], SiblingNodes]
"""Mapping of sibling nodes to hierarchal categories sorted as per the schema."""

type NodeName = str
"""Name of the node, containing info on it's ranks for categories and subcategories 
and its bucket. Used for physical storage of the databank."""

type NodePics = list[EvaluatedPic]
"""Evaluated images within a node."""

type NodeBucket = str
"""Bucket marker for to differinteate sibling nodes. Examples A, B..., or
ABC, ABD, ABE..."""

type SortedMarks = tuple[int, ...]
"""Evaluation marks of categories sorted as per the schema."""

type MustResize = bool
"""Indicator if the image should be resized (upon physical save) to save storage space
or, if not, to preserve HD texture detail."""


class EvaluatedPic:
    """Encapsulates evaluations for an image with info on where it is stored."""
    output_folder = DEFAULT_OUTPUT

    def __init__(
        self,
        storage_path: ImageStoragePath,
        categories: Categories | None = None,
        evals: Evaluations | None = None,
        resize: MustResize = True,
    ) -> None:
        """Initialize the object with all attributes."""
        self.storage_path = os.path.normcase(storage_path)
        if categories is None:
            self.categories: Categories = []
        else:
            self.categories = categories
        if evals is None:
            self.__evals: Evaluations = {}
        else:
            self.__evals = evals
        self.resize = resize

        self.node_ref: ImageStorageNode | None = None

    def add_category(
        self, category: EvalCategory, category_priority: PrioritizedCategories
    ) -> None:
        """Add a category that the image fits into."""
        if category not in self.categories:
            self.categories.append(category)
            self.__sort_categories(category_priority)

    def __sort_categories(self, category_priority: PrioritizedCategories) -> None:
        """Sort categories according to schema priorities."""
        image_cat_idx = 0
        for cat in category_priority:
            if cat in self.categories:
                cur_idx = self.categories.index(cat)
                self.categories[cur_idx] = self.categories[image_cat_idx]
                self.categories[image_cat_idx] = cat
                image_cat_idx += 1

    def evaluate(self, category: EvalCategory, mark: Mark) -> None:
        """Add or change an evaluation for the image."""
        self.__evals[category] = mark

    @property
    def evals(self) -> Evaluations:
        """Get a copy of numerical evaluations with corresponding evaluation
        category names for the image.
        """
        return self.__evals.copy()

    @evals.setter
    def evals(self, new_evals: Evaluations | None = None) -> None:
        """Set new or reset numerical evaluations with corresponding evaluation
        category names for the image.
        """
        self.__evals = new_evals if new_evals else {}

    @property
    def sorted_marks(self) -> SortedMarks:
        """Evaluation marks for the categories assigned for the image."""
        return tuple(self.__evals[mark] for mark in self.categories)

    def physical_process(self, node_name: NodeName) -> None:
        """Process physical storage of the image. If category hierarchy didn't
        change do nothing. If other image with that name exists - rename.
        Assumes that the system never repeats the same datetime.
        """
        relative_path = (
            os.path.join(*self.categories)
            if len(self.categories) > 0
            else DEFAULT_UNCATEGORIZED_OUTPUT
        )
        os.makedirs(self.output_folder, exist_ok=True)
        new_path = os.path.join(self.output_folder, relative_path, node_name)
        os.makedirs(new_path, exist_ok=True)
        new_file_path = full_path_from_relative(
            file=self.storage_path, 
            new_relative_path=new_path
        )

        if os.path.isfile(new_file_path):
            suffix = datetime.now().strftime("%Y%m%dT%H%M%S")
            new_file_path = full_path_from_relative(
                file=self.storage_path, new_relative_path=new_path, suffix=suffix
            )

        if not self.resize and new_file_path == self.storage_path:
            return

        self.storage_path = transfer_image(
            file=self.storage_path, new_file_path=new_file_path, resize=self.resize
        )

        if self.resize:
            self.resize = False


class ImageStorageNode:
    """A node to store evaluated image objects differentiated by categories."""

    def __init__(
        self,
        name: NodeName | None = None,
        ranks: SortedMarks | None = None,
        bucket: NodeBucket | None = None,
        evaluated_pics: NodePics | None = None,
    ) -> None:
        """Instantiate the node with possible rank and json data for pics."""
        if name is not None:
            self.__name = name
            components = name.split("_")
            if bucket is None:
                self.bucket: NodeBucket = components.pop(-1)
            if ranks is None:
                self.ranks: SortedMarks = tuple(map(int, components))
        else:
            self.__name = None

        if ranks is not None:
            self.ranks = ranks
        if bucket is not None:
            self.bucket = bucket

        if evaluated_pics is None:
            self.images: NodePics = []
        else:
            self.images: NodePics = evaluated_pics
            for image in self.images:
                image.node_ref = self

    @property
    def name(self) -> NodeName:
        """The name of this node."""
        if self.__name is None:
            name = [str(rank) for rank in self.ranks]
            name.append(self.bucket)
            self.__name = "_".join(name)
        return self.__name

    def add_image(self, image: EvaluatedPic) -> bool:
        """Add image object to the node. Returns true if the image was added."""
        if image.node_ref == self:
            if image.resize:
                image.physical_process(node_name=self.name)
            return True

        if len(self.images) >= MAX_ITEMS_PER_NODE:
            return False
        
        if image.node_ref is not None:
            image.node_ref.pop_image(image)
        self.images.append(image)
        image.node_ref = self
        image.physical_process(node_name=self.name)

        return True

    def pop_image(self, pic: EvaluatedPic) -> None:
        """Pop image from the node."""
        index = self.__index_image(pic)
        if index is not None:
            self.images.pop(index)

    def __index_image(self, pic: EvaluatedPic) -> int | None:
        """Looks for an image in NodePics images list."""
        if pic in self.images:
            return self.images.index(pic)
        raise ValueError("Evaluated Pic object was not found in this Node.")


class ImageNodesHolder:
    """Parent for image nodes that maps nodes to their respective categories."""

    def __init__(self, image_nodes: NodesCatsMap | None = None) -> None:
        """Initialize node container."""
        if image_nodes is not None:
            self.image_nodes = image_nodes
        else:
            self.image_nodes: NodesCatsMap = {}

    def list_images(self) -> list[EvaluatedPic]:
        all_nodes: list[ImageStorageNode] = [
            node for sibling in self.image_nodes.values() for node in sibling
        ]
        all_node_images: list[EvaluatedPic] = [
            image for node in all_nodes for image in node.images
        ]

        return all_node_images

    def post_pic(self, image: EvaluatedPic) -> None:
        """Fits the image object based on its attributes.

        Takes into account primary category, all present subcategories and their
        respective evaluations. Appropriate nodes are found by category/subcategory
        path.

        If several nodes match the criteria (same categories, but different evals
        and buckets), finds the one that has empty space for the image.

        If a fitting node does not exist, creates it.

        Asserts categories of the EvaluatedPic are sorted as per the schema.
        """
        nodes_key = (
            tuple(image.categories)
            if len(image.categories) > 0
            else (DEFAULT_UNCATEGORIZED_OUTPUT,)
        )

        sibling_nodes = self.image_nodes.get(nodes_key)
        if not sibling_nodes:
            sibling_nodes = []
            self.image_nodes[nodes_key] = sibling_nodes

        fitting_mark_nodes = [
            node for node in sibling_nodes if node.ranks == image.sorted_marks
        ]

        for node in fitting_mark_nodes:
            if node.add_image(image):
                return
        else:
            buckets = [node.bucket for node in fitting_mark_nodes]
            if len(buckets) > 0:
                max_bucket = list(max(buckets))
                ordinal = ord(max_bucket[-1]) + 1
                max_bucket[-1] = chr(ordinal)
                bucket = "".join(max_bucket)
            else:
                bucket = "a"

            new_node = ImageStorageNode(
                ranks=image.sorted_marks,
                bucket=bucket,
            )
            new_node.add_image(image)
            sibling_nodes.append(new_node)
