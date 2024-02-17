import json
import os

from databank_schema import DataBankSchema
from file_utils import filter_files
from image_nodes import (EvaluatedPic, ImageNodesHolder, ImageStorageNode,
                         NodePics, NodesPathMap, SiblingNodes)

STORAGE_FORMAT = "json"
DEFAULT_DB_PATH = "databank"
DEFAULT_ENCODING = "utf-8"
JSON_INDENT = 4


class JSONDataBank:
    """Responsible for saving evaluated image info to a physical storage in JSON."""

    @classmethod
    def read(cls, path: str = DEFAULT_DB_PATH) -> ImageNodesHolder:
        """Read the databank folder.

        The root must contain folder structure fitting categories and json files
        with lists of evaluated images data.
        """
        image_nodes: NodesPathMap = {}
        for folder, _, files in os.walk(path):
            if len(files) == 0:
                continue
            rel_path = os.path.relpath(folder, start=path)
            files = filter_files(files, STORAGE_FORMAT)

            nodes: SiblingNodes = []
            for file in files:
                full_path = os.path.join(folder, file)
                with open(full_path, "r", encoding=DEFAULT_ENCODING) as fstream:
                    eval_pics_json_data = json.load(fstream)
                node_name = os.path.basename(full_path).split(".")[0]

                images: NodePics = [
                    EvaluatedPic(
                        storage_path=pic.get(DataBankSchema.storage_path),
                        categories=pic.get(DataBankSchema.categories),
                        evals=pic.get(DataBankSchema.evals),
                    )
                    for pic in eval_pics_json_data
                ]

                nodes.append(
                    ImageStorageNode(
                        name=node_name,
                        evaluated_pics=images,
                    )
                )
            image_nodes[rel_path] = nodes
        return ImageNodesHolder(image_nodes)

    @staticmethod
    def save(
        nodes_holder: ImageNodesHolder,
        root_path: str = DEFAULT_DB_PATH,
    ):
        """Save node structure to the databank folder.

        The root contains folder structure fitting categories and json files
        with lists of evaluated images data.
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
