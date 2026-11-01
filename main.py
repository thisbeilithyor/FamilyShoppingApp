from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.anchorlayout import MDAnchorLayout

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.storage.jsonstore import JsonStore

import requests
from datetime import datetime

class EinkaufApp(MDApp):
    pass

class MyScreenManager(MDScreenManager):
    pass

class IdentifyWidget(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = JsonStore('data.json')
        try:
            if self.data.get('user')['name']!="":
                Clock.schedule_once(self.switch_screen_username_is_set, 0)
        except:
            pass
            
    def fertig_btn(self, text_input):
        if(text_input!=""):
            self.data.put('user', name=text_input)
            app = MDApp.get_running_app()
            app.root.current = 'main_screen' 

    def switch_screen_username_is_set(self, dt):
        app = MDApp.get_running_app()
        app.root.current = 'main_screen'



class MainWidget(MDScreen):
    # firebase_url = 'https://YOURFIREBASEURLRIGHTHERE.firebasedatabase.app/einkaufsliste.json'
    artikel = []
    gridlayout = GridLayout(cols=1, spacing=10, size_hint_y=None)
    scrollview = MDScrollView(size_hint=(0.94, 0.8), pos_hint={"center_x": 0.5, "center_y": 0.48})
    mdanchorlayout = MDAnchorLayout(anchor_x='right', anchor_y='bottom', padding=[0, 0, dp(5), dp(5)])
    namelayout = MDAnchorLayout(anchor_x='left', anchor_y='bottom', padding=[dp(5),0,0,0])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_pre_enter(self):
        self.load_einkaufsliste()

    def load_einkaufsliste(self):
        self.gridlayout.clear_widgets()
        self.scrollview.clear_widgets()
        self.clear_widgets()

        res = requests.get(self.firebase_url)
        if res.status_code == 200:
            data = res.json()
            if data:
                for item_id, item in data.items():
                    username = item['username']
                    my_item = item['item']
                    time = item['time']
                    self.artikel.append({'id': item_id, 'username': username, 'my_item': my_item, 'time': time})
    
            self.artikel = self.artikel[::-1]

            self.gridlayout.bind(minimum_height = self.gridlayout.setter("height"))
            for a in self.artikel:
                factory = ArtikelFactory()
                factory.load_artikel(a, self.artikel_deleted_callback)
                self.gridlayout.add_widget(factory)
            self.scrollview.add_widget(self.gridlayout)
            self.add_widget(self.scrollview)

            self.artikel = []
        
        tb = MDTopAppBar(title="schweiger einkauf", pos_hint={"top": 1}, right_action_items=[["refresh", lambda x: self.load_einkaufsliste()]])
        self.add_widget(tb)
        
        add_btn = Button(
            size_hint=(None, None),
            size=(dp(50), dp(50)),
            text="+",
            background_color=(0, 1, 0, 1),
            on_release=self.switch_to_newitem_screen
        )
        self.mdanchorlayout.add_widget(add_btn)
        self.add_widget(self.mdanchorlayout)

        try:
            data = JsonStore('data.json')
            username = data.get('user')['name']
        except:
            username ="user"

        name_label = MDLabel(
            size_hint=(None, None),
            size=(dp(200), dp(50)),
            text="Angemeldet als: "+username,
            on_release=self.refresh
        )
        self.namelayout.add_widget(name_label)
        self.add_widget(self.namelayout)
    
    def refresh(self, instance):
        self.load_einkaufsliste()
        
    def artikel_deleted_callback(self):
        self.load_einkaufsliste()
        
    def switch_to_newitem_screen(self, instance):
        app = MDApp.get_running_app()
        app.root.current = 'newitem_screen' 

class ArtikelFactory(MDBoxLayout):
    # firebase_url = 'https://YOURFIREBASEURLRIGHTHERE.firebasedatabase.app/einkaufsliste.json'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, None)
        self.height = dp(50)

    def load_artikel(self, artikel, delete_callback):
        username = artikel["username"]
        item_name = artikel["my_item"]
        time = artikel["time"]
        self.item_id =artikel["id"]
        self.delete_callback = delete_callback

        info_box = MDBoxLayout(size_hint_x=0.2, orientation='vertical')
        item_box = MDBoxLayout(size_hint_x=0.6)
 
        username_label = MDLabel(text=self.string_shortener(username))
        time_label = MDLabel(text=time)
        info_box.add_widget(username_label)
        info_box.add_widget(time_label)

        item_label = MDLabel(text=item_name, font_size=15)
        item_box.add_widget(item_label)

        delete_button = MDIconButton(text="x", icon="trash-can")
        delete_button.bind(on_press=self.delete)

        self.add_widget(info_box)
        self.add_widget(item_box)
        self.add_widget(delete_button)

    def string_shortener(self, string):
        if len(string) > 5:
            return string[:5]
        else:
            return string

    def delete(self, instance):
        res = requests.get(self.firebase_url)
        data = res.json()
        if self.item_id in data:
            del data[self.item_id]
            requests.put(self.firebase_url, json=data)
            if self.delete_callback:
                self.delete_callback()

class NewItemScreen(MDScreen):
    # firebase_url = 'https://YOURFIREBASEURLRIGHTHERE.firebasedatabase.app/einkaufsliste.json'
    def add_btn(self, artikel_input):
        if artikel_input!="":
            current_time = datetime.now()
            current_time_hours_minutes = current_time.strftime("%H:%M")

            try:
                data = JsonStore('data.json')
                username = data.get('user')['name']
            except:
                username ="user"

            data = {
                "username": username, 
                "item": artikel_input, 
                "time": current_time_hours_minutes
            }
            res = requests.post(url=self.firebase_url+"einkaufsliste.json", json=data)
            self.ids.artikel_input.text = ""
            
            app = MDApp.get_running_app()
            app.root.current = 'main_screen'
    
    def back_btn(self):
        app = MDApp.get_running_app()
        app.root.current = 'main_screen'

if __name__ == "__main__":
    EinkaufApp().run()