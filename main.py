import socket
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from threading import Thread

class PerformerClient(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        
        # Interfejs
        self.ip_input = TextInput(text='192.168.1.100', multiline=False, size_hint_y=0.1)
        self.btn = Button(text='Połącz', size_hint_y=0.1)
        self.btn.bind(on_press=self.toggle_connection)
        
        self.image = Image(size_hint_y=0.8)
        
        self.add_widget(self.ip_input)
        self.add_widget(self.btn)
        self.add_widget(self.image)
        
        self.is_connected = False
        self.sock = None

    def toggle_connection(self, instance):
        if not self.is_connected:
            self.is_connected = True
            self.btn.text = 'Rozłącz'
            Thread(target=self.receive_stream, daemon=True).start()
        else:
            self.is_connected = False
            self.btn.text = 'Połącz'

    def receive_stream(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.ip_input.text, 36000))
            
            while self.is_connected:
                header = self.sock.recv(28)
                if len(header) < 28:
                    break
                
                # Odczyt protokołu HY37
                magic = int.from_bytes(header[0:4], byteorder='little')
                codec = int.from_bytes(header[4:8], byteorder='little')
                size = int.from_bytes(header[8:12], byteorder='little')
                
                payload = bytearray()
                while len(payload) < size:
                    packet = self.sock.recv(size - len(payload))
                    if not packet:
                        break
                    payload.extend(packet)
                
                if magic == 0x48593337 and codec == 1:
                    # Aktualizacja obrazu w wątku głównym
                    Clock.schedule_once(lambda dt: self.update_image(bytes(payload)))
        except Exception as e:
            print(f"Błąd: {e}")
        finally:
            self.is_connected = False
            Clock.schedule_once(lambda dt: setattr(self.btn, 'text', 'Połącz'))

    def update_image(self, data):
        # Wczytanie bajtów JPEG bezpośrednio do tekstury Kivy
        try:
            import io
            from PIL import Image as PILImage
            img = PILImage.open(io.BytesIO(data))
            img = img.convert('RGBA')
            
            texture = Texture.create(size=(img.width, img.height), colorfmt='rgba')
            texture.blit_buffer(img.tobytes(), colorfmt='rgba', bufferfmt='ubyte')
            texture.flip_vertical()
            self.image.texture = texture
        except Exception:
            pass

class MainApp(App):
    def build(self):
        return PerformerClient()

if __name__ == '__main__':
    MainApp().run()
  
