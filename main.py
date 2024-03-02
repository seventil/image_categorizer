import os

from kivy.app import App
from kivy.core.window import Window
from kivy.logger import Logger
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen

from app_logic import OnScreenImageHandler
from databank import JSONDataBank
from eval_schema import EvaluationSchema, LabeledCheckBox
from file_utils import DEFAULT_DATABANK_DIR, DEFAULT_OUTPUT

Logger.setLevel("DEBUG")
ZOOM_IN_SCALE = 1.75
ZOOM_OUT_SCALE = 0.4
DEFAULT_IMAGE = "Kivy-logo.jpg"


class MainScreen(Screen):
    """Main App screen that shows an Image and checkboxes for its evlauation."""

    screen_name = "main_screen"

    def __init__(self, **kwargs) -> None:
        """Initialize a screen object with evaluation schema and corresponding checkboxes."""
        super(MainScreen, self).__init__(name=MainScreen.screen_name)
        Window.bind(on_keyboard=self._on_keyboard)

        running_app: MainApp = App.get_running_app()  # type: ignore
        self.eval_schema: EvaluationSchema = running_app.evaluation_schema

        self.__set_up_evaluation_checkboxes()

    def _on_keyboard(self, *args):
        LEFT_KEY = 276
        RIGHT_KEY = 275
        UP_KEY = 273
        DOWN_KEY = 274

        if args[1] == LEFT_KEY:
            self._load_previous_image()
        if args[1] == RIGHT_KEY:
            self._load_next_image()
        if args[1] == UP_KEY:
            self.scale_image(ZOOM_IN_SCALE)
        if args[1] == DOWN_KEY:
            self.scale_image(ZOOM_OUT_SCALE)

    def on_enter(self, *args) -> None:
        """When entering this screen render an image."""
        Logger.info("Entering main screen")
        self.__load_new_image()

    def on_leave(self, *args) -> None:
        """When leaving this screen save the evaluations."""
        self.image_handler.save_current()
        self.image_handler.save_eval_data()
        self.ids.image.source = DEFAULT_IMAGE

    def _on_zoom_in(self):
        self.scale_image(ZOOM_IN_SCALE)

    def _on_zoom_out(self):
        self.scale_image(ZOOM_OUT_SCALE)

    def _on_resize_check_box(self, active: bool):
        Logger.info(f"_on_resize_check_box {active}")
        self.image_handler.current.resize = active

    def scale_image(self, scale: float = 1):
        img = self.ids.image
        x, y = img.size
        img.size = (x * scale, y * scale)
        img.center_x = img.parent.parent.center_x
        img.center_y = img.parent.parent.center_y
        self.ids.scatter_img_holder.pos = self.ids.stencil1.pos

    def set_image_handler(self, handler: OnScreenImageHandler) -> None:
        """Set the image handler for this screen."""
        self.image_handler = handler

    def _load_previous_image(self) -> None:
        """Save current evaluated image to appropriate Node,
        save it physically and load prev image.
        """
        self.image_handler.save_current()
        self.image_handler.previous()
        self.__load_new_image()

    def _load_next_image(self) -> None:
        """Save current evaluated image to appropriate Node,
        save it physically and load next image.
        """
        self.image_handler.save_current()
        self.image_handler.next()
        self.__load_new_image()

    def __load_new_image(self) -> None:
        """Reload current image and reload evaluation checkboxes."""
        img = self.ids.image
        self.ids.scatter_img_holder.pos = self.ids.stencil1.pos
        img.size = self.ids.stencil1.width, self.ids.stencil1.height

        self.eval_schema.reload_evaluations(self.image_handler.current.evals)
        self.ids.img_name.text = self.image_handler.current.storage_path

        img.source = self.image_handler.current.storage_path
        img.center_x = img.parent.parent.center_x
        img.center_y = img.parent.parent.center_y
        self.ids.resize_check_box.active = self.image_handler.current.resize

    def __set_up_evaluation_checkboxes(self) -> None:
        """Dynamically add evaluation checkboxes using eval_schema.

        When creating checkboxes in a category should check up on databank.
        """
        eval_box: BoxLayout = self.ids.eval_box
        for cat in self.eval_schema.total_evals:
            category_vbox = BoxLayout(orientation="vertical")

            category_label = Label(text=cat)
            category_vbox.add_widget(category_label)

            category_checks_hbox = BoxLayout(orientation="horizontal")
            category_vbox.add_widget(category_checks_hbox)

            for mark in range(1, 1 + self.eval_schema.eval_range_for_categories[cat]):
                check_label = Label(text=str(mark))

                check = LabeledCheckBox(group=cat, active=False, label=mark)
                self.eval_schema.assign_checks(cat, mark, check)
                check.bind(on_release=self._on_checkbox_active)  # type: ignore

                category_checks_hbox.add_widget(check_label)
                category_checks_hbox.add_widget(check)

            eval_box.add_widget(category_vbox)

    def _on_checkbox_active(self, checkbox: LabeledCheckBox) -> None:
        """Update image evaluations and, if needed, give it a new category."""
        if checkbox.group in self.eval_schema.prioritized_categories:
            self.image_handler.current.add_category(
                checkbox.group, self.eval_schema.prioritized_categories
            )
        self.image_handler.current.evaluate(checkbox.group, checkbox.label)

    def _on_reset_evals(self) -> None:
        """Resets UI checkboxes and evaluation in the image."""
        self.eval_schema.reset_current_evals()
        self.image_handler.current.evals = {}
        self.image_handler.current.categories.clear()
        self.image_handler.save_current()


class MenuScreen(Screen):
    """Screen that allows to scan folder or databank for images to evaluate."""

    def on_enter(self, *args):
        Logger.info("Entering menu screen")

    def _load_databank(self) -> None:
        """Load eval image info from databank and go through its images."""
        self.__process_scan_inputs(DEFAULT_OUTPUT)

    def _load_inputs(self) -> None:
        """Load a list of images in a user-specified directory."""
        user_input_path: str = (
            self.ids.inputs_text.text or self.ids.inputs_text.hint_text
        )
        self.__process_scan_inputs(user_input_path)

    def __process_scan_inputs(self, input_path: str) -> None:
        nodes_holder = None
        input_path = os.path.normcase(input_path)
        dirs = input_path.split(os.path.sep)
        if dirs[0] == DEFAULT_OUTPUT:
            dirs.insert(1, DEFAULT_DATABANK_DIR)
            path = os.path.join(*dirs)
            nodes_holder = JSONDataBank.read(path)

        image_handler = OnScreenImageHandler(input_path, nodes_holder)
        if image_handler.empty:
            popup = Popup(
                title="Folder scan warning",
                content=Label(text="The input path does not contain images"),
                auto_dismiss=True,
                size_hint=(0.4, 0.4),
            )
            popup.open()
            return

        self.parent.get_screen(MainScreen.screen_name).set_image_handler(image_handler)
        self.parent.current = MainScreen.screen_name


class MainApp(App):
    """Main kivy app."""

    def __init__(self, *args, **kwargs) -> None:
        """Initiate the kivy app object and read eval schema."""
        super().__init__(*args, **kwargs)
        self.evaluation_schema = EvaluationSchema()

    def on_stop(self) -> None:
        self.root.current_screen.on_leave()  # type: ignore


if __name__ == "__main__":
    MainApp().run()
