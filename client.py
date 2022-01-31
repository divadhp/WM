"""
Encargado de pintar una ventana con los decoradores necesarios. Incluye las operaciones necesarias para 
transformar las ventanas, como resize.
"""

from Xlib import X


class Client:

    def __init__(self, window):

        self.window = window

    def map(self):
        self.window.map()

    def unmap(self):
        self.window.unmap()

    def change_attributes(self, mask):
        self.window.change_attributes(event_mask=mask)

    def focus(self):
        self.window.set_input_focus(X.RevertToParent, 0)
        self.window.configure(stack_mode=X.Above)

    def above(self):
        self.window.configure(stack_mode=X.Above)

    def configure(self, x=0, y=0, width=300, height=300):
        self.window.configure(x=x, y=y, width=width, height=height)
