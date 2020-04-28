#!/usr/bin/env python3
import json
import os
import gi
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, GLib


PLUGINS = {}


def get_apps_windows():
    s = Wnck.Screen.get_default()
    s.force_update()  # so libwnck reads all the window details
    data = {}
    for w in s.get_windows():
        if w.get_window_type() != Wnck.WindowType.NORMAL: continue
        app = w.get_application()
        pid = w.get_pid()
        if pid == 0: continue
        if pid not in data:
            data[pid] = {
                "name": app.get_name(),
                "windows": []
            }
        geo = w.get_geometry()
        window_data = {
            "title": w.get_name(),
            "window": w,
            "x": geo.xp,
            "y": geo.yp,
            "width": geo.widthp,
            "height": geo.heightp
        }
        data[pid]["windows"].append(window_data)
    return data


def add_command_lines(data):
    for pid in data:
        app_name = data[pid]["name"]
        if app_name in PLUGINS:
            data[pid]["command_line"] = PLUGINS[app_name](data[pid])
        else:
            with open("/proc/{}/cmdline".format(pid), 'rt') as fp:
                cmdline = fp.read()
                cmdline = cmdline.replace("\x00", " ")
                data[pid]["command_line"] = cmdline.strip()
    return data


def tidy(data):
    ndata = {}
    for pid in data:
        appname = data[pid]["name"]
        if appname in ndata:
            count = 1
            while True:
                nappname = "{} ({})".format(appname, count)
                if nappname not in ndata: break
                count += 1
            appname = nappname

        for w in data[pid]["windows"]:
            del w["window"]
        del data[pid]["name"]

        ndata[appname] = data[pid]
    return ndata


def save(data):
    out = os.path.join(GLib.get_user_config_dir(), "appremember")
    with open(out, mode="w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2)


def main():
    app_windows = get_apps_windows()
    decorated = add_command_lines(app_windows)
    serialisable = tidy(decorated)
    save(serialisable)


if __name__ == "__main__":
    main()
