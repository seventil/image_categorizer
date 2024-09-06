""" This module has unit-tests for image_nodes module, written in three styles.
One assumes that unit may be wide and checks behaviour given the input. 
This means one unit includes not only a method call, but all the nested calls
and all the side-effects. Uses mocks for external dependencies.
The second style is the same as the first one, but uses real objects
for injected dependencies instead of mocks.
The last style assumes that unit is the smallest executable part, avoids side
effects and tries mocking every nested and injected functionality.
"""
import os
import shutil
import sys
from pathlib import Path
from unittest import TestCase, main

from PIL import Image

sys.path.append(str(Path(__file__).resolve().parent.parent))

from file_utils import MAX_SIZE
from image_nodes import MAX_ITEMS_PER_NODE, EvaluatedPic, ImageStorageNode

TEST_PIC_PATH = "./tests/test_assets/1.jpg"

class TestAddImageNarrow(TestCase):
    """This class covers testing ImageStorageNode.add_image
    in a shallow way, basically checking with 100% test coverage that
    the 'right' code paths/branching exist"""
    class EPicMock:
        def __init__(self):
            self.physical_processed = False
            self.node_ref = None

        def physical_process(self, *args, **kwargs):
            self.physical_processed = kwargs["node_name"]

    class NodeMock:
        def __init__(self):
            self.image_popped = False

        def pop_image(self, *args, **kwargs):
            self.image_popped = True

    def setUp(self) -> None:
        self.epic = self.EPicMock()
        self.epic2 = self.EPicMock()
        self.isn = ImageStorageNode(name="A")
        self.isn2 = ImageStorageNode(name="B")
        self.isn3 = self.NodeMock()

    def test_same_img_resize(self):
        self.epic.resize = True
        self.epic.node_ref = self.isn
        self.assertTrue(self.isn.add_image(self.epic))
        self.assertTrue(self.epic.physical_processed)

    def test_same_img_not_resize(self):
        self.epic.resize = False
        self.epic.node_ref = self.isn
        self.assertTrue(self.isn.add_image(self.epic))
        self.assertFalse(self.epic.physical_processed)

    def test_max_imgs_in_node(self):
        self.isn.images = [x for x in range(MAX_ITEMS_PER_NODE)]
        self.assertFalse(self.isn.add_image(self.epic))

    def test_path_invariant_pic_has_ref(self):
        self.epic.resize = False
        self.epic.node_ref = self.isn
        test_path = "test/path"
        self.epic.storage_path = test_path
        self.assertTrue(self.isn.add_image(self.epic))
        self.assertEqual(self.epic.storage_path, test_path)

    def test_node_ref_popped(self):
        self.epic.node_ref = self.isn3
        self.assertFalse(self.isn3.image_popped)
        self.assertTrue(self.isn.add_image(self.epic))
        self.assertTrue(self.isn3.image_popped)

    def test_node_images_appended(self):
        self.epic.node_ref = self.isn3
        before_adding = len(self.isn.images)
        self.assertTrue(self.isn.add_image(self.epic))
        self.assertEqual(len(self.isn.images), before_adding + 1)
  

class TestAddImageWideReal(TestCase):
    """This class covers testing ImageStorageNode.add_image
    method. It basically checks that given inputs
    the necessary code branching is present and we see
    desired state changes in coupled systems (in this case
    it's the file system)."""

    def setUp(self) -> None:
        self.test_output = "tests/test_assets/add_image"
        self.test_output2 = "tests/test_assets/add_image/abc"
        os.makedirs(self.test_output, exist_ok=True)
        os.makedirs(self.test_output2, exist_ok=True)
        self.bigger_pic_test_path = f"{self.test_output}/test_big.jpg"
        self.second_pic_test_path = f"{self.test_output2}/test_big.jpg"
        shutil.copy(TEST_PIC_PATH, self.bigger_pic_test_path)
        shutil.copy(TEST_PIC_PATH, self.second_pic_test_path)
        with Image.open(self.bigger_pic_test_path) as img:
            img = img.resize((int(MAX_SIZE*1.2), int(MAX_SIZE*1.2)))
            img.save(self.bigger_pic_test_path)
        
        self.isn = ImageStorageNode(name="A")
        self.epic = EvaluatedPic(self.bigger_pic_test_path)
        self.epic.output_folder = self.test_output
        self.isn2 = ImageStorageNode(name="B")
        self.epic2 = EvaluatedPic(self.second_pic_test_path, ["abc"])
        self.epic2.output_folder = self.test_output
        
        return super().setUp()
    
    def tearDown(self) -> None:
        shutil.rmtree(self.test_output) 
        shutil.rmtree(self.test_output2, ignore_errors=True)
        return super().tearDown()

    def test_same_img_resize(self):
        """This test duplicates testing for
        EvaluatedPic.physical_process resize
        functionality. Basically would be a duplicate,
        but since ImageStorageNode.add_image is the only
        consumer, it doesn't need a separate check. It
        either works together or it doesn't work at all. 
        It has too many nuances of execution paths to account for and that
        had to be hardcoded.
        """
        self.epic.resize = True
        self.assertTrue(self.isn.add_image(self.epic))

        with Image.open(self.epic.storage_path) as img:
            self.assertEqual(img.size[0], MAX_SIZE)

    def test_same_img_not_resize(self):
        self.epic.resize = False
        self.assertTrue(self.isn.add_image(self.epic))

        with Image.open(self.epic.storage_path) as img:
            self.assertGreater(img.size[0], MAX_SIZE)

    def test_max_imgs_in_node(self):
        self.isn.images = [x for x in range(MAX_ITEMS_PER_NODE)]
        self.epic.node_ref = self.isn2
        self.assertFalse(self.isn.add_image(self.epic))

    def test_path_invariant_pic_has_ref(self):
        self.epic.resize = False
        self.epic.node_ref = self.isn

        self.assertTrue(self.isn.add_image(self.epic))
        self.assertEqual(self.epic.storage_path, self.bigger_pic_test_path)

    def test_path_variant_pic_other_ref(self):
        self.isn2.add_image(self.epic)
        first_path = self.epic.storage_path

        self.assertTrue(self.isn.add_image(self.epic))
        self.assertNotEqual(first_path, self.epic.storage_path)

    def test_suffix_added_on_conflict(self):
        self.isn.add_image(self.epic)
        self.isn2.add_image(self.epic2)
        self.assertEqual(
            os.path.basename(self.epic.storage_path), 
            os.path.basename(self.epic2.storage_path)
        )
        self.epic2.categories.pop()
        
        self.assertTrue(self.isn.add_image(self.epic2))
        self.assertEqual(
            os.path.dirname(self.epic.storage_path),
            os.path.dirname(self.epic2.storage_path)
        )
        self.assertNotEqual(
            os.path.basename(self.epic.storage_path), 
            os.path.basename(self.epic2.storage_path)
        )

if __name__ == "__main__":
    main()
