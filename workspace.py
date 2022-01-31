"""
Encargado de representar un workspace. Estos wokspaces tienen una lista de clientes y un layout activo.
"""
from Xlib import X
from client import Client
from layout import Layout

class Workspace:

    def __init__(self, width, height):

        # Diccionario de clientes, llave window, item frame
        self.clients = []
        self.current_client = 0

        self.width = width
        self.height = height
        self.layout = Layout(self.width, self.height)

    def find_geometry(self, window):
        return None

    def apply_layout(self):
        self.layout.apply(self.clients)

    def manage(self, window):
        print("Map")
        if self.get_client(window):
            return
        c = Client(window)
        self.clients.append(c)
        self.apply_layout()
        c.map()

        mask = X.EnterWindowMask | X.LeaveWindowMask
        c.change_attributes(mask)
        self.current_client = self.clients.index(c)

    def focus(self, window):
        c = self.get_client(window)
        if c:
            self.current_client = self.clients.index(c)
            c.focus()

    def unmanage(self, window):
        c = self.get_client(window)

        if c:
            self.clients.remove(c)
            self.apply_layout()

    def configure(self, event):
        window = event.window
        x, y = event.x, event.y
        width, height = event.width, event.height
        mask = event.value_mask

        # c = self.get_client(window)

        if mask == 0b1111:
            window.configure(x=x, y=y, width=width, height=height)
        elif mask == 0b1100:
            window.configure(width=width, height=height)
        elif mask == 0b0011:
            window.configure(x=x, y=y)
        elif mask == 0b01000000:
            window.configure(event.stack_mode)
         

    def get_client(self, window):

        for c in self.clients:
            if c.window == window:
                return c
        return None

    def maximize_focused(self):
        print(self.current_client)
        self.clients[self.current_client].configure(x=0, y=0, width=self.width, height=self.height)
        self.clients[self.current_client].above()

    def hide(self):
        for c in self.clients:
            c.unmap()

    def show(self):
        for c in self.clients:
            c.map()
