from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager

from app_logic import ListCursor, scan_images_input

Window.size=(1028,640)
Builder.load_file('main_app.kv')


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(name=kwargs.get('name'))
        self.images_to_evaluate = []
        self.cursor = None

    def on_enter(self):
        self.images_to_evaluate = scan_images_input()
        if len(self.images_to_evaluate) > 0:
            self.cursor = ListCursor(len(self.images_to_evaluate))
            self.__load_new_image()
        else:
            raise NotImplementedError("input scan folder is empty")

    def on_leave(self):
        pass

    def _load_previous_image(self):
        self.cursor << 1
        self.__load_new_image()

    def _load_next_image(self):
        self.cursor >> 1
        self.__load_new_image()

    def __load_new_image(self):
        new_image = self.images_to_evaluate[int(self.cursor)]
        self.ids.img_name.text = new_image
        self.ids.image.source = new_image


class MainApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main_screen'))
        return sm

if __name__=='__main__':
    MainApp().run()
