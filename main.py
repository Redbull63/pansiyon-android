# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button

class TestApp(App):
    def build(self):
        layout = BoxLayout(orientation="vertical", padding=20, spacing=20)
        layout.add_widget(Label(
            text="Merhaba Pansiyon!", font_size=40, color=(0.1,0.2,0.4,1)))
        layout.add_widget(Label(
            text="APK çalışıyor ✓\n\nTürkçe: ığşçöüİĞŞÇÖÜ",
            font_size=20))
        layout.add_widget(Button(
            text="Kapat", font_size=24, size_hint_y=None, height=80,
            on_release=lambda x: App.get_running_app().stop()))
        return layout

if __name__ == "__main__":
    TestApp().run()
