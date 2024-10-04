import json
import os

from databank_schema import DataBankSchema
from file_utils import DEFAULT_DB_PATH, filter_files
from image_nodes import (EvaluatedPic, ImageNodesHolder, ImageStorageNode,
                         NodePics, NodesCatsMap, SiblingNodes)

STORAGE_FORMAT = "json"

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
        image_nodes: NodesCatsMap = {}
        for folder, _, files in os.walk(path):
            if len(files) == 0:
                continue
            rel_path = os.path.relpath(folder, start=DEFAULT_DB_PATH)

            node_key = tuple(rel_path.split(os.path.sep))
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
                        resize=pic.get(DataBankSchema.resize),
                        tags=pic.get(DataBankSchema.tags),
                    )
                    for pic in eval_pics_json_data
                ]

                nodes.append(
                    ImageStorageNode(
                        name=node_name,
                        evaluated_pics=images,
                    )
                )
            image_nodes[node_key] = nodes
        return ImageNodesHolder(image_nodes)

    @staticmethod
    def save(
        nodes_holder: ImageNodesHolder,
        append: bool,
        root_path: str = DEFAULT_DB_PATH,
    ):
        """Save node structure to the databank folder.

        The root contains folder structure fitting categories and json files
        with lists of evaluated images data.
        Append mode if the inputs were read without accessing the databank,
        write mode if the databank was read completely and the file has to be fully
        updated.
        """

        for path, image_nodes in nodes_holder.image_nodes.items():
            for node in image_nodes:
                evaluated_images = []
                for img in node.images:
                    evaluated_img_json = {
                        DataBankSchema.storage_path: img.storage_path,
                        DataBankSchema.categories: img.categories,
                        DataBankSchema.evals: img.evals,
                        DataBankSchema.resize: img.resize,
                        DataBankSchema.tags: img.tags,
                    }
                    evaluated_images.append(evaluated_img_json)
                output_name = f"{node.name}.{STORAGE_FORMAT}"
                output_path = os.path.join(root_path, *path)
                os.makedirs(output_path, exist_ok=True)
                full_file_path = os.path.join(output_path, output_name)
                mode = "a" if append else "w"

                with open(
                    full_file_path,
                    mode,
                    encoding=DEFAULT_ENCODING,
                ) as fstream:
                    json.dump(evaluated_images, fstream, indent=JSON_INDENT)
