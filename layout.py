"""
Encargado de calcular el layout mediante una lista de clientes aportada por el workspace.
"""

class Layout:
    """ Clase encargada de posicionar cada ventana."""

    def __init__(self, width, height):

        self.name = "layout"
        self.width = width
        self.height = height

    def __str__(self):
        return self.name

    def apply(self, clients):
        nx = 0
        ny = 0
        nw = self.width
        nh = self.height

        if len(clients) > 1:
        
            for i, c in enumerate(clients):
                if i < len(clients) - 1:
                    if i % 2:
                        nh /= 2
                    else:
                        nw /= 2
                if i % 4 == 0:
                    ny += nh
                elif i % 4 == 1:
                    nx += nw
                elif i % 4 == 2:
                    ny += nh
                elif i % 4 == 3:
                    nx += nw

                if i == 0:
                    ny = 30
                elif i == 1:
                    nx = self.width - nw

                c.configure(x=int(nx),
                            y=int(ny),
                            width=int(nw),
                            height=int(nh))
        elif len(clients) == 1:
            c = clients[0]
            c.configure(x=nx, y=ny, width=nw, height=nh)
            

        
    
