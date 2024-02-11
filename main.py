from kivy.app import App
from kivy.logger import Logger
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen

from app_logic import (DEFAULT_EVAL_RANGE, EvaluationSchema, ListCursor,
                       scan_images_input)
from image_nodes import EvaluatedPic

Logger.setLevel("DEBUG")
APP_UI_TEMPLATE_FILE = "main_app.kv"


class LabeledCheckBox(CheckBox):
    def __init__(self, **kwargs):
        super(LabeledCheckBox, self).__init__(**kwargs)

    label = ObjectProperty(None, allownone=True)


class MainScreen(Screen):
    screen_name = "main_screen"

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(name=MainScreen.screen_name)
        self.images_to_evaluate = []
        self.cursor = None
        self.eval_schema: EvaluationSchema = App.get_running_app().evaluation_schema

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

    def on_enter(self):
        self.__load_new_image()

    def on_leave(self):
        pass

    def _on_checkbox_active(self, checkbox) -> None:
        if checkbox.group in self.eval_schema.priority_categories:
            self.current_eval_entity.add_category(
                checkbox.group, self.eval_schema.priority_categories
            )
        self.current_eval_entity.evaluate(checkbox.group, checkbox.label)

    def _load_previous_image(self):
        self.cursor << 1
        self.__load_new_image()

    def _load_next_image(self):
        self.cursor >> 1
        self.__load_new_image()

    def __load_new_image(self):
        self.__assign_current_eval_entity()
        self.__reload_evaluations()
        self.ids.img_name.text = self.current_eval_entity.storage_path
        self.ids.image.source = self.current_eval_entity.storage_path

    def __assign_current_eval_entity(self) -> None:
        new_image = self.images_to_evaluate[int(self.cursor)]
        if not isinstance(new_image, EvaluatedPic):
            self.current_eval_entity = EvaluatedPic(new_image)
            self.images_to_evaluate[int(self.cursor)] = self.current_eval_entity
        else:
            self.current_eval_entity = new_image

    def __reload_evaluations(self) -> None:
        for eval_category in self.eval_schema.total_evals:
            eval_checkboxes = self.eval_schema.get_checks(eval_category)
            cur_entity_eval = self.current_eval_entity.evals.get(eval_category)
            for checkbox in eval_checkboxes.values():
                checkbox.active = False
            if cur_entity_eval is not None:
                eval_checkboxes[cur_entity_eval].active = True


class MenuScreen(Screen):
    def _load_databank(self):
        self.parent.current = MainScreen.screen_name

    def _load_inputs(self):
        user_input_path = self.ids.inputs_text.text or self.ids.inputs_text.hint_text
        
        images_to_evaluate: list[str | EvaluatedPic] = scan_images_input(user_input_path)
        if len(images_to_evaluate) == 0:
            popup = Popup(
                title='Folder scan warning', 
                content=Label(text='The input path does not contain images'),
                auto_dismiss=True,
                size_hint=(0.4, 0.4)
            )
            popup.open()
            return

        scrs = self.parent.get_screen(MainScreen.screen_name)
        scrs.images_to_evaluate = images_to_evaluate
        scrs.cursor = ListCursor(len(images_to_evaluate))

        self.parent.current = MainScreen.screen_name


class MainApp(App):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.evaluation_schema = EvaluationSchema()


if __name__ == "__main__":
    MainApp().run()
