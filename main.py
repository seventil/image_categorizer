from kivy.app import App
from kivy.logger import Logger
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen

from app_logic import DEFAULT_EVAL_RANGE, OnScreenImageHandler
from eval_schema import EvaluationSchema, LabeledCheckBox

Logger.setLevel("DEBUG")
APP_UI_TEMPLATE_FILE = "main_app.kv"


class MainScreen(Screen):
    screen_name = "main_screen"

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(name=MainScreen.screen_name)

        self.image_handler: OnScreenImageHandler | None = None
        self.eval_schema: EvaluationSchema = App.get_running_app().evaluation_schema

        self.__set_up_evaluation_checkboxes()

    def on_enter(self):
        self.__load_new_image()

    def on_leave(self):
        pass

    def set_image_handler(self, handler: OnScreenImageHandler) -> None:
        self.image_handler = handler

    def _load_previous_image(self):
        self.image_handler.previous()
        self.__load_new_image()

    def _load_next_image(self):
        self.image_handler.next()
        self.__load_new_image()

    def __load_new_image(self):
        self.eval_schema.reload_evaluations(self.image_handler.current.evals)
        self.ids.img_name.text = self.image_handler.current.storage_path
        self.ids.image.source = self.image_handler.current.storage_path

    def __set_up_evaluation_checkboxes(self) -> None:
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
                check.bind(on_release=self._on_checkbox_active)

                category_checks_hbox.add_widget(check_label)
                category_checks_hbox.add_widget(check)

            eval_box.add_widget(category_vbox)

    def _on_checkbox_active(self, checkbox) -> None:
        if checkbox.group in self.eval_schema.prioritized_categories:
            self.image_handler.current.add_category(
                checkbox.group, self.eval_schema.prioritized_categories
            )
        self.image_handler.current.evaluate(checkbox.group, checkbox.label)


class MenuScreen(Screen):
    def _load_databank(self):
        self.parent.current = MainScreen.screen_name
        raise NotImplementedError("databank is not ready")

    def _load_inputs(self):
        user_input_path = self.ids.inputs_text.text or self.ids.inputs_text.hint_text
        image_handler = OnScreenImageHandler(user_input_path)
        
        if image_handler.empty:
            popup = Popup(
                title='Folder scan warning', 
                content=Label(text='The input path does not contain images'),
                auto_dismiss=True,
                size_hint=(0.4, 0.4)
            )
            popup.open()
            return

        self.parent.get_screen(MainScreen.screen_name).set_image_handler(image_handler)
        self.parent.current = MainScreen.screen_name


class MainApp(App):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.evaluation_schema = EvaluationSchema()


if __name__ == "__main__":
    MainApp().run()
