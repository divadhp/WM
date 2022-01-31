"""
Gestor de ventanas. Incluye una lista de workspaces, solo una es visible por monitor. Incluye una barra que se puede ocultar en cualquier momento.
"""

import sys
import os
import subprocess
from theme import Theme
from workspace import Workspace
from Xlib import X, display, XK
from Xlib.ext import shape
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

KEYSYM_TBL = {
    'XF86AudioRaiseVolume': 0x1008ff13,
    'XF86AudioLowerVolume': 0x1008ff11
}

MOD = X.Mod1Mask

KEYBOARD_HANDLER = {
    'm': {
        'modifier': MOD,
        'method': 'maximize_focused'
    },
    '1': {
        'modifier': MOD,
        'method': 'move_workspace',
        'args': 0
    },
    '2': {
        'modifier': MOD,
        'method': 'move_workspace',
        'args': 1
    },
    'p': {
        'modifier': MOD,
        'command': 'rofi',
        'args': ['-show', 'run']
    },
    't': {
        'modifier': MOD,
        'command': 'xterm'
    },
    'e': {
        'modifier': MOD | X.ShiftMask,
        'command': 'emacs'
    },
    'f': {
        'modifier': MOD | X.ShiftMask,
        'command': 'firefox'
    },
    # for debugging
    'r': {
        'modifier': X.Mod1Mask | X.ControlMask,
        'method': 'restart'
    },
    'q': {
        'modifier': MOD | X.ShiftMask,
        'method': 'exit'
    },
}

def hex_to_rgb(hex):
    hex = hex.lstrip('#')
    rgb = tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))

    return (rgb[0]<<16) | (rgb[1]<<8) | (rgb[2])
    

class WindowManager:
    def __init__(self, display):
        self.display = display
        self.screen = self.display.screen(0)
        self.colormap = self.screen.default_colormap
        self.key_handlers = {}


        self.restart = False

        self.init_workspaces()
        self.event_handler = {
            X.KeyPress: self.key_press,
            X.ButtonPress: self.button_press,
            X.ButtonRelease: self.button_release,
            X.MapRequest: self.map_request,
            X.MapNotify: self.map_notify,
            X.UnmapNotify: self.unmap_notify,
            X.DestroyNotify: self.destroy_notify,
            X.ConfigureRequest: self.configure_request,
            X.EnterNotify: self.enter_notify,
            X.MotionNotify: self.motion_notify
        }

        self.tinit = time.time()

        self.drag_window = None
        self.drag_button = None
        self.drag_geometry = None
        self.drag_start_xy = None
        self.drag_last_time = 0

        self.running = True

    def get_screen_size(self):
        """Return the dimension (WIDTH, HEIGHT) of the current screen as a
        tuple in pixels.  If xrandr command exsits and either DP (DisplayPort)
        or HDMI output is active, return its dimensionn instead of the screen
        size of the current X11 display."""
        width, height = self.screen.width_in_pixels, self.screen.height_in_pixels
        # output = subprocess.getoutput('xrandr --current')
        # # pick the last line including DP- or HDMI-
        # m = re.search(r'(DP-?\d|HDMI-?\d) connected (\d+)x(\d+)', output)
        # if m:
        #     width, height = int(m.group(2)), int(m.group(3))
        # # limit the screen size if sendscreen/record-desktop is running
        # code, output = subprocess.getstatusoutput('pidof -x sendscreen')
        # if code == 0:
        #     width, height = 800, 600
        # code, output = subprocess.getstatusoutput('pidof -x record-desktop')
        # if code == 0:
        #     width, height = 800, 600
        # debug('get_screen_size -> w:%d h:%d', width, height)
        return width, height

    def init_workspaces(self):
        self.workspaces = [Workspace(*self.get_screen_size()) for i in range(Theme.num_workspaces)]
        self.curr_workspace = 0

    def move_workspace(self, i):
        print("Move to workspace", i)
        self.workspaces[self.curr_workspace].hide()
        self.curr_workspace = i
        self.workspaces[self.curr_workspace].show()

    def maximize_focused(self):
        self.workspaces[self.curr_workspace].maximize_focused()

    def grab_keys(self):
        """Configure the root window to receive key inputs according to the
        key definitions `KEYBOARD_HANDLER'.  Also, the jump table is stored in
        `self.key_handlers'."""
        for string, entry in KEYBOARD_HANDLER.items():
            keysym = XK.string_to_keysym(string)
            # FIXME: use keysymdef/xf86.py
            if not keysym and string in KEYSYM_TBL:
                keysym = KEYSYM_TBL[string]
            keycode = self.display.keysym_to_keycode(keysym)
            if not keycode:
                continue

            modifier = entry.get('modifier', X.NONE)
            self.screen.root.grab_key(keycode, modifier, True, X.GrabModeAsync,
                                      X.GrabModeAsync)
            self.key_handlers[keycode] = entry

    def grab_buttons(self):
        """Configure the root window to receive mouse button events."""
        for button in [1, 3]:
            self.screen.root.grab_button(button, X.Mod1Mask, True,
                                         X.ButtonPressMask, X.GrabModeAsync,
                                         X.GrabModeAsync, X.NONE, X.NONE)

    def key_press(self, event):
        keycode = event.detail
        print(keycode)
        entry = self.key_handlers.get(keycode, None)
        if not entry:
            # self.running = False
            return

        args = entry.get('args', None)
        if 'method' in entry:
            method = getattr(self, entry['method'], None)
            if method:
                if args is not None:
                    method(args)
                else:
                    method()
        elif 'function' in entry:
            function = globals().get(entry['function'], None)
            if function:
                if args is not None:
                    function(args)
                else:
                    function()
        elif 'command' in entry:
            comm = entry['command']
            if args is not None:
                subprocess.Popen([comm] + args)
            else:
                subprocess.Popen(entry['command'])
        # self.running = False

    def exit(self):
        self.running = False

    def restart(self):
        self.running = False
        self.restart = True


    def map_request(self, event):
        print("Map")
        self.workspaces[self.curr_workspace].manage(event.window)
        self.workspaces[self.curr_workspace].focus(event.window)

    def map_notify(self, event):
        # self.workspaces[self.curr_workspace].manage(event.window)
        pass

    def unmap_notify(self, event):
        self.workspaces[self.curr_workspace].unmanage(event.window)

    def destroy_notify(self, event):
        # self.workspaces[self.curr_workspace].unmanage(event.window)
        pass

    def configure_request(self, event):
        self.workspaces[self.curr_workspace].configure(event)

    def enter_notify(self, event):
        self.workspaces[self.curr_workspace].focus(event.window)

    def motion_notify(self, event):
        x, y = event.root_x, event.root_y
        # prevent to reposition window too frequently
        if time.time() - self.drag_last_time <= 1 / 60:
            return
        self.drag_last_time = time.time()

        dx = x - self.drag_start_xy[0]
        dy = y - self.drag_start_xy[1]
        if self.drag_button == 1:
            # reposition
            self.drag_window.configure(x=self.drag_geometry.x + dx,
                                       y=self.drag_geometry.y + dy)
            # dragging further might switch the virtual screen
            # self._may_switch_virtual_screen(x, y)
        else:
            # resize
            self.drag_window.configure(
                width=max(300, self.drag_geometry.width + dx),
                height=max(300, self.drag_geometry.height + dy))
        # self.draw_frame_windows(self.drag_window)

    def button_press(self, event):
        """Initiate window repositioning with the button 1 or window resizing
        with the button 3.  All mouse pointer motion events are captured until
        the button is relased."""
        window = event.child
        self.screen.root.grab_pointer(
            True, X.PointerMotionMask | X.ButtonReleaseMask, X.GrabModeAsync,
            X.GrabModeAsync, X.NONE, X.NONE, 0)
        self.drag_window = window
        self.drag_button = event.detail
        # FIXME: drag_geometry might be None
        self.drag_geometry = window.get_geometry()#self.get_window_geometry(window)
        self.drag_start_xy = event.root_x, event.root_y

    def button_release(self, event):
        self.display.ungrab_pointer(0)

    def start(self):
        # Code executed before the start only once
        # TODO: add wallpaper
        subprocess.Popen(["bash", "/home/divadhp/.fehbg"])
        subprocess.Popen("picom")
        subprocess.Popen(["setxkbmap", "es"])

        self.width, self.height = self.get_screen_size()
        # colormap = self.screen.default_colormap
        # pixel = colormap.alloc_named_color('aquamarine1').pixel
        # window = self.screen.root.create_window(0, 0, self.width, 30, 3, self.screen.root_depth, X.InputOutput, pixel,override_redirect=True)
        # window.map()
        bgsize = 20

        bgpm = self.screen.root.create_pixmap(
            bgsize,
            bgsize,
            self.screen.root_depth
        )
        
        print("Pixel")
        print(self.screen.black_pixel)
        print(self.screen.white_pixel)
        print(hex_to_rgb("#ffffff"))


        bggc = self.screen.root.create_gc(
            foreground=hex_to_rgb('#4c566a'),
            background=hex_to_rgb('#4c566a')
        )

        bgpm.fill_rectangle(bggc, 0, 0, bgsize, bgsize)

        bggc.change(foreground=hex_to_rgb('#5e81ac'), background=hex_to_rgb('#4c566a'))

        # bgpm.arc(bggc, -bgsize // 2, 0, bgsize, bgsize, 0, 360 * 64)
        bgpm.arc(bggc, 0, 0, bgsize, bgsize, 0, 360*64)
        # bgpm.arc(bggc, 0, -bgsize // 2, bgsize, bgsize, 0, 360 * 64)
        # bgpm.arc(bggc, 0, bgsize // 2, bgsize, bgsize, 0, 360 * 64)

        # Actual window
        self.window = self.screen.root.create_window(
            0, 0, (bgsize)+1, bgsize+1, 0,
            self.screen.root_depth,
            X.InputOutput,
            X.CopyFromParent,

            # special attribute values
            background_pixmap=bgpm,
            event_mask=(
                X.StructureNotifyMask |
                X.ButtonReleaseMask
            ),
            colormap=X.CopyFromParent
        )

        self.add_size = 21

        self.add_pm = self.window.create_pixmap(self.add_size, self.add_size, 1)
        gc = self.add_pm.create_gc(foreground = 0, background = 0)
        self.add_pm.fill_rectangle(gc, 0, 0, self.add_size, self.add_size)
        gc.change(foreground = 1)
        self.add_pm.fill_arc(gc, 0, 0, self.add_size, self.add_size, 0, 360 * 64)
        gc.free()

        self.sub_size = 19
        self.sub_pm = self.window.create_pixmap(self.sub_size, self.sub_size, 1)
        gc = self.sub_pm.create_gc(foreground = 0, background = 0)
        self.sub_pm.fill_rectangle(gc, 0, 0, self.sub_size, self.sub_size)
        gc.change(foreground = 1)
        self.sub_pm.fill_poly(gc, X.Convex, X.CoordModeOrigin,
                              [(self.sub_size // 2, 0),
                               (self.sub_size, self.sub_size // 2),
                               (self.sub_size // 2, self.sub_size),
                               (0, self.sub_size // 2)])
        gc.free()
        self.window.shape_mask(shape.SO.Set, shape.SK.Bounding,
                               0, 0, self.add_pm)
        self.window.shape_mask(shape.SO.Union, shape.SK.Bounding,
                               20 - self.add_size, 0, self.add_pm)
        self.window.shape_mask(shape.SO.Union, shape.SK.Bounding,
                               0, 20 - self.add_size, self.add_pm)
        self.window.shape_mask(shape.SO.Union, shape.SK.Bounding,
                               20 - self.add_size, 20 - self.add_size,
                               self.add_pm)

        # Tell X server to send us mask events
        self.window.shape_select_input(1)

        
        # self.window.map()

    def catch_events(self):
        """Configure the root window to receive all events needed for managing windows."""
        mask = (X.SubstructureRedirectMask | X.SubstructureNotifyMask
                | X.EnterWindowMask | X.LeaveWindowMask | X.FocusChangeMask)
        self.screen.root.change_attributes(event_mask=mask)

    def loop(self):
        print("Start running")

        while self.running:
            # Get last event
            event = self.display.next_event()
            print(event)

            try:
                self.event_handler[event.type](event)
            except KeyError:
                print("Error")
                print(event.type)
                # self.running = False
                # sys.exit()
            if (time.time() - self.tinit) > 6000:
                print("Run out of time")
                # self.running = False
                # sys.exit()

    def run(self):
        self.catch_events()
        self.grab_keys()
        self.grab_buttons()
        self.start()
        self.loop()

        if self.restart:
            subprocess.Popen('/home/divadhp/Proyectos/py_wm/start.sh')


if __name__ == '__main__':
    WindowManager(display.Display()).run()
