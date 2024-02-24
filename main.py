from kivy.app import App
from kivy.core.window import Window
from kivy.logger import Logger
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen

from app_logic import DEFAULT_EVAL_RANGE, OnScreenImageHandler
from databank import JSONDataBank
from eval_schema import EvaluationSchema, LabeledCheckBox
from file_utils import DEFAULT_OUTPUT

Logger.setLevel("DEBUG")
APP_UI_TEMPLATE_FILE = "main_app.kv"


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

        if args[1] == LEFT_KEY:
            self._load_previous_image()
        if args[1] == RIGHT_KEY:
            self._load_next_image()

    def on_enter(self, *args) -> None:
        """When entering this screen render an image."""
        Logger.info("Entering main screen")
        self.__load_new_image()

    def on_leave(self, *args) -> None:
        """When leaving this screen save the evaluations."""
        self.image_handler.save_current()
        self.image_handler.save_eval_data()

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
        self.eval_schema.reload_evaluations(self.image_handler.current.evals)
        self.ids.img_name.text = self.image_handler.current.storage_path
        self.ids.image.source = self.image_handler.current.storage_path

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

            for mark in range(1, 1 + DEFAULT_EVAL_RANGE):
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
        self.parent.current = MainScreen.screen_name
        nodes_holder = JSONDataBank.read()
        image_handler = OnScreenImageHandler(DEFAULT_OUTPUT, nodes_holder)

        if image_handler.empty:
            popup = Popup(
                title="Databank warning",
                content=Label(text="Databank contains no physical images"),
                auto_dismiss=True,
                size_hint=(0.4, 0.4),
            )
            popup.open()
            return

        self.parent.get_screen(MainScreen.screen_name).set_image_handler(image_handler)
        self.parent.current = MainScreen.screen_name

    def _load_inputs(self) -> None:
        """Load a list of images in a user-specified directory."""
        user_input_path: str = (
            self.ids.inputs_text.text or self.ids.inputs_text.hint_text
        )
        image_handler = OnScreenImageHandler(user_input_path)

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
