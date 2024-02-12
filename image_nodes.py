
import os

from databank_schema import DataBankSchema
from eval_schema import Categories, Evaluations, PrioritizedCategories

MAX_ITEMS_PER_NODE = 1000

IMAGE_FILE_FORMATS = ["jpg", "jpeg", "png", "webp"]

type CategoryHierarchyPath = str
type SiblingNodes = list[ImageStorageNode]
type NodesPathMap = dict[CategoryHierarchyPath, SiblingNodes]
type NodeName = str
type NodeRef = tuple[CategoryHierarchyPath, NodeName]
type NodePics = list[EvaluatedPic]
type SortedRanks = tuple[int, ...]


class EvaluatedPic:
    """Encapsulates evaluations for an image with info on where it is stored.

    Attributes:
        storage_path (str): describes where the image is storred.
        categories (Categories): categories (from schema) that the image fits.
        evals (Evaluations): evaluations that where set for the image.
        resize (bool): if the image should be resized to save storage space.
            Defaults to True. Should be set to False if high-definition texture
            is important.
    """

    def __init__(
        self,
        storage_path: str,
        categories: Categories | None = None,
        evals: Evaluations | None = None,
        resize: bool = True,
    ) -> None:
        """Initialize the object with all attributes.

        Args:
            storage_path (str): describes where the image is storred.
            categories (Categories | None): categories (from schema) that the image fits.
            evals (Evaluations | None): evaluations that where set for the image.
            resize (bool): if the image should be resized (on physical save) 
                to save storage space. Defaults to True. Should be set to False 
                if high-definition texture is important.
        """
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

        self.__current_node_ref: ImageStorageNode = None

    def add_category(self, category: str, category_priority: PrioritizedCategories) -> None:
        """Add a category that the image fits into.

        Args:
            category (str): name of the category from the schema file.
            category_priority (PrioritizedCategories): sorted categories from schema, where
                lowest index indicates higher folder (closer to root) in the databank
                structure.
        """
        if category not in self.categories:
            self.categories.append(category)
            self.__sort_categories(category_priority)

    def __sort_categories(self, category_priority: PrioritizedCategories) -> None:
        """Sort categories according to schema priorities.

        Args:
            category_priority (PrioritizedCategories): sorted categories from schema, where
                lowest index indicates higher folder (closer to root) in the databank
                structure.self.__evals
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
        self.__evals[category] = mark

    @property
    def evals(self) -> Evaluations:
        return self.__evals.copy()
    
    @evals.setter
    def evals(self, new_evals: Evaluations | None = None) -> None:
        self.__evals = new_evals if new_evals else {}

    @property
    def sorted_ranks(self) -> SortedRanks:
        return (self.__evals[rank] for rank in self.categories)
    
    @property
    def node_ref(self) -> "ImageStorageNode":
        return self.__current_node_ref
    
    @node_ref.setter
    def node_ref(self, new_node: "ImageStorageNode"):
        self.__current_node_ref = new_node


class ImageStorageNode:
    """A node to store evaluated image objects differentiated by categories.

    Attributes:
        ranks (SortedRanks | None): category mark of the images contained in the node.
        bucket (str | None): bucket that splits the images by MAX_ITEMS_PER_NODE.
        name (NodeName | None): name of the node, containing info on it's ranks for
            categories and subcategories and its bucket.
        images (SiblingNodes): evaluated images.
    """

    def __init__(
        self,
        name: NodeName | None = None,
        ranks: SortedRanks | None = None,
        bucket: str | None = None,
        evaluated_pics: list[dict] | None = None,
    ) -> None:
        """Instantiate the node with possible rank and json data for pics.

        Args:
            name (str | None): name of the node. Defaults to None.
            ranks (SortedRanks | None): category mark of the images contained in the node. Defaults to None.
            bucket (str | None): bucket that splits the images by MAX_ITEMS_PER_NODE. Defaults to None.
            evaluated_pics (list[dict] | None): json data for pics. Defaults to None.
        """
        if name is not None:
            self.__name: NodeName = name
            name = name.split("_")
            self.bucket: str = name.pop(-1)
            self.ranks: SortedRanks = tuple(map(int, name))
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
        image.node_ref.pop_image(image)
        self.images.append(image)
        image.node_ref = self
        return True

    def pop_image(self, pic: EvaluatedPic) -> None:
        """Pop image from the node."""
        index = self.__index_image(pic)
        self.images.pop(index)
    
    def __index_image(self, pic: EvaluatedPic) -> int | None:
        """Looks for an image in NodePics images list.

        Returns:
            int: index if image is present.
        """
        if pic in self.images:
            return self.images.index(pic)
        raise ValueError("Evaluated Pic object was not found in this Node.")


class ImageNodesHolder:
    """Parent for image nodes that maps nodes to their respective categories.

    Attributes:
        image_nodes (NodesPathMap): mapping of nodes to categories.
    """

    def __init__(self, image_nodes: NodesPathMap) -> None:
        """Initialize node container.

        Args:
            image_nodes (Dict[str, NodesPathMap]): mapping of image nodes
                with their categories in hierarchy notation.
        """
        self.__image_nodes = image_nodes

    @property
    def image_nodes(self) -> NodesPathMap:
        """Image nodes property.

        Returns:
            NodesPathMap mapping of image nodes with their
                categories in hierarchy notation.
        """
        return self.__image_nodes

    def post_pic(self, image: EvaluatedPic) -> None:
        """Fits the image object based on its attributes.

        Takes into account primary category, all present subcategories and their
        respective evaluations. Appropriate nodes are found by category/subcategory
        path.
        
        If several nodes match the criteria (same categories, but different evals
        and buckets), finds the one that has empty space for the image.

        If a fitting node does not exist, creates it.

        Asserts categories of the EvaluatedPic are sorted as per the schema.

        Args:
            image (EvaluatedPic): image the node is searched for.
        """
        relative_path = os.path.join(image.categories)
        sibling_nodes = self.__image_nodes.get(relative_path)
        if not sibling_nodes:
            sibling_nodes = []
            self.__image_nodes[relative_path] = sibling_nodes

        fitting_mark_nodes = [
            node
            for node in sibling_nodes
            if node.ranks == image.sorted_ranks
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
                ranks=image.sorted_ranks, 
                bucket=bucket,
            )
            new_node.add_image(image)
            sibling_nodes.append(new_node)
