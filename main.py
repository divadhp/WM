from importlib import reload
import theme
from theme import Theme
import sys

while True:
    del sys.modules['theme']

    reload(theme)

    from theme import Theme
    theme = Theme()

    print(theme.text)
