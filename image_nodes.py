
import os

from databank_schema import DataBankSchema
from eval_schema import (Categories, Eval_Category, Evaluations, Mark,
                         PrioritizedCategories)

MAX_ITEMS_PER_NODE = 1000

IMAGE_FILE_FORMATS = ["jpg", "jpeg", "png", "webp"]

type CategoryHierarchyPath = str

type ImageStoragePath = str
"""Full path to the image. Consists of scan directory + Optional(CategoryHierarchyPath)
 + file name."""

type SiblingNodes = list[ImageStorageNode]
"""A list of nodes with the same assigned categories."""

type NodesPathMap = dict[CategoryHierarchyPath, SiblingNodes]
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
    def __init__(
        self,
        storage_path: ImageStoragePath,
        categories: Categories | None = None,
        evals: Evaluations | None = None,
        resize: MustResize = True,
    ) -> None:
        """Initialize the object with all attributes."""
        self.storage_path = storage_path
        if categories is None:
            self.categories = []
        else:
            self.categories = categories
        if evals is None:
            self.__evals = {}
        else:
            self.__evals = evals
        self.resize = resize

        self.node_ref: ImageStorageNode = None

    def add_category(self, category: Eval_Category, category_priority: PrioritizedCategories) -> None:
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

    def evaluate(self, category: Eval_Category, mark: Mark) -> None:
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
        return (self.__evals[mark] for mark in self.categories)


class ImageStorageNode:
    """A node to store evaluated image objects differentiated by categories."""

    def __init__(
        self,
        name: NodeName | None = None,
        ranks: SortedMarks | None = None,
        bucket: NodeBucket | None = None,
        evaluated_pics: list[dict] | None = None,
    ) -> None:
        """Instantiate the node with possible rank and json data for pics."""
        if name is not None:
            self.__name: NodeName = name
            name = name.split("_")
        if name is not None and bucket is None:
            self.bucket: NodeBucket = name.pop(-1)
        if name is not None and ranks is None:
            self.ranks: SortedMarks = tuple(map(int, name))
        if ranks is not None:
            self.ranks = ranks
        if bucket is not None:
            self.bucket = bucket

        if evaluated_pics is None:
            self.images: NodePics = []
        else:
            self.images: NodePics = [
                EvaluatedPic(
                    storage_path=pic.get(DataBankSchema.storage_path),
                    categories=pic.get(DataBankSchema.categories),
                    evals=pic.get(DataBankSchema.evals),
                )
                for pic in evaluated_pics
            ]

    @property
    def name(self) -> NodeName:
        """The name of this node."""
        if not self.__name:
            name = [rank for rank in self.ranks]
            name.append(self.bucket)
            self.__name = "_".join(name)
        return self.__name

    def add_image(self, image: EvaluatedPic) -> bool:
        """Add image object to the node. Returns true if the image was added."""
        if len(self.images > MAX_ITEMS_PER_NODE):
            return False
        image.node_ref.pop_image(image)
        self.images.append(image)
        image.node_ref = self
        return True

    def pop_image(self, pic: EvaluatedPic) -> None:
        """Pop image from the node."""
        index = self.__index_image(pic)
        self.images.pop(index)
    
    def __index_image(self, pic: EvaluatedPic) -> int | None:
        """Looks for an image in NodePics images list."""
        if pic in self.images:
            return self.images.index(pic)
        raise ValueError("Evaluated Pic object was not found in this Node.")


class ImageNodesHolder:
    """Parent for image nodes that maps nodes to their respective categories."""
    def __init__(self, image_nodes: NodesPathMap) -> None:
        """Initialize node container."""
        self.image_nodes = image_nodes

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
        relative_path = os.path.join(image.categories)
        sibling_nodes = self.image_nodes.get(relative_path)
        if not sibling_nodes:
            sibling_nodes = []
            self.image_nodes[relative_path] = sibling_nodes

        fitting_mark_nodes = [
            node
            for node in sibling_nodes
            if node.ranks == image.sorted_marks
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
                bucket = "A"

            new_node = ImageStorageNode(
                ranks=image.sorted_marks, 
                bucket=bucket,
            )
            new_node.add_image(image)
            sibling_nodes.append(new_node)
