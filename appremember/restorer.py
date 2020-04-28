#!/usr/bin/env python3
import json
import os
import gi
import time
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, GLib


MAXIMUM_TIME_TO_LOOK = 5  # seconds
RESIZE_MASK = (Wnck.WindowMoveResizeMask.X | Wnck.WindowMoveResizeMask.Y |
               Wnck.WindowMoveResizeMask.WIDTH | Wnck.WindowMoveResizeMask.HEIGHT)


class Restorer():
    def __init__(self, loop):
        self.loop = loop
        apps = self.load()
        windows = []
        for app in apps:
            self.launch(apps[app])
            for w in apps[app]["windows"]:
                nw = {"appname": app}
                nw.update(w)
                windows.append(nw)

        GLib.timeout_add_seconds(1, self.spin_until_done, windows)

    def load(self):
        t = time.time()
        inp = os.path.join(GLib.get_user_config_dir(), "appremember")
        with open(inp, mode="r", encoding="utf-8") as fp:
            data = json.load(fp)
        for appname in data:
            for w in data[appname]["windows"]:
                w["started_looking"] = t
        return data

    def launch(self, app):
        print("Now I would run this command line:", app["command_line"])

    def spin_until_done(self, saved_windows):
        if not saved_windows:
            self.loop.quit()
            return False

        # Get windows on screen
        screen_windows = []
        s = Wnck.Screen.get_default()
        s.force_update()  # so libwnck reads all the window details
        for w in s.get_windows():
            if w.get_window_type() != Wnck.WindowType.NORMAL: continue
            app = w.get_application()
            pid = w.get_pid()
            if pid == 0: continue
            screen_windows.append((app.get_name(), w.get_name(), w))

        # Check each window
        t = time.time()
        nwindows = []
        for w in saved_windows:
            # see if this is in screen windows
            matching_screen_windows = [sw for sw in screen_windows
                if sw[0] == w["appname"] and sw[1] == w["title"]]
            if len(matching_screen_windows) == 0:
                pass
            elif len(matching_screen_windows) > 1:
                pass
            else:
                an, wn, sw = matching_screen_windows[0]
                print("restoring position for", an, wn)
                sw.set_geometry(Wnck.WindowGravity.CURRENT, RESIZE_MASK,
                    w["x"], w["y"], w["width"], w["height"])
                continue  # don't add to list for continued looking

            # If we've been looking too long, give up
            age = t - w["started_looking"]
            if age > MAXIMUM_TIME_TO_LOOK: continue  # don't add to list

            nwindows.append(w)

        saved_windows[:] = nwindows

        return True


if __name__ == "__main__":
    loop = GLib.MainLoop()
    restorer = Restorer(loop)
    loop.run()

