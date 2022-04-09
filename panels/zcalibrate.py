#flsun modify ,all page content are modified ,for a new z adjust page
import gi
import logging
import re

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

from ks_includes.KlippyGcodes import KlippyGcodes
from ks_includes.screen_panel import ScreenPanel

def create_panel(*args):
    return ZCalibratePanel(*args)

class ZCalibratePanel(ScreenPanel):
    user_selecting = False

    bs = 0
    bs_delta = "0.05"
    bs_deltas = ["0.01", "0.05", "0.1"]
    #percent_delta = 1
    #percent_deltas = ['1', '5', '10', '25']
    #fan = 100

    #extrusion = 0
    #speed = 0

    def initialize(self, panel_name):
        _ = self.lang.gettext

        grid = self._gtk.HomogeneousGrid()
        grid.set_row_homogeneous(False)
        logging.debug("ZCalibratePanel")

        print_cfg = self._config.get_printer_config(self._screen.connected_printer)
        if print_cfg is not None:
            bs = print_cfg.get("z_babystep_values", "0.01, 0.05, 0.1")
            if re.match(r'^[0-9,\.\s]+$', bs):
                bs = [str(i.strip()) for i in bs.split(',')]
                if len(bs) <= 2:
                    self.bs_deltas = bs
                else:
                    self.bs_deltas = [bs[0], bs[-1]]
                self.bs_delta = self.bs_deltas[0]

        self.labels['Move_Z0'] = self._gtk.ButtonImage("arrow-down", _("Move Z0"), "color2")
        self.labels['Move_Z0'].connect("clicked", self.Move_Z0)

        grid.attach(self.labels['Move_Z0'], 0, 0, 1, 1)

        self.labels['z+'] = self._gtk.ButtonImage("z-farther", _("Z+"), "color1")
        self.labels['z+'].connect("clicked", self.change_babystepping, "+")
        self.labels['zoffset'] = Gtk.Label("0.00" + _("mm"))
        self.labels['zoffset'].get_style_context().add_class('temperature_entry')
        self.labels['z-'] = self._gtk.ButtonImage("z-closer", _("Z-"), "color1")
        self.labels['z-'].connect("clicked", self.change_babystepping, "-")

        grid.attach(self.labels['z+'], 1, 0, 1, 1)
        grid.attach(self.labels['zoffset'], 1, 1, 1, 1)
        grid.attach(self.labels['z-'], 1, 2, 1, 1)

        #self.labels['speed+'] = self._gtk.ButtonImage("speed+", _("Speed +"), "color3")
        #self.labels['speed+'].connect("clicked", self.change_speed, "+")
        #self.labels['speedfactor'] = Gtk.Label("100%")
        #self.labels['speedfactor'].get_style_context().add_class('temperature_entry')
        #self.labels['speed-'] = self._gtk.ButtonImage("speed-", _("Speed -"), "color3")
        #self.labels['speed-'].connect("clicked", self.change_speed, "-")
        #grid.attach(self.labels['speed+'], 1, 0, 1, 1)
        #grid.attach(self.labels['speedfactor'], 1, 1, 1, 1)
        #grid.attach(self.labels['speed-'], 1, 2, 1, 1)

        #self.labels['extrude+'] = self._gtk.ButtonImage("flow+", _("Extrusion +"), "color4")
        #self.labels['extrude+'].connect("clicked", self.change_extrusion, "+")
        #self.labels['extrudefactor'] = Gtk.Label("100%")
        #self.labels['extrudefactor'].get_style_context().add_class('temperature_entry')
        #self.labels['extrude-'] = self._gtk.ButtonImage("flow-", _("Extrusion -"), "color4")
        #self.labels['extrude-'].connect("clicked", self.change_extrusion, "-")
        #grid.attach(self.labels['extrude+'], 2, 0, 1, 1)
        #grid.attach(self.labels['extrudefactor'], 2, 1, 1, 1)
        #grid.attach(self.labels['extrude-'], 2, 2, 1, 1)


        # babystepping grid
        bsgrid = Gtk.Grid()
        j = 0
        for i in self.bs_deltas:
            self.labels[i] = self._gtk.ToggleButton(i)
            self.labels[i].connect("clicked", self.change_bs_delta, i)
            ctx = self.labels[i].get_style_context()
            if j == 0:
                ctx.add_class("distbutton_top")
            elif j == len(self.bs_deltas)-1:
                ctx.add_class("distbutton_bottom")
            else:
                ctx.add_class("distbutton")
            if i == self.bs_delta:
                ctx.add_class("distbutton_active")
            bsgrid.attach(self.labels[i], j, 0, 1, 1)
            j += 1
        grid.attach(bsgrid, 1, 3, 1, 1)

        # self.panel = grid
        self.content.add(grid)

    def process_update(self, action, data):
        _ = self.lang.gettext

        if action != "notify_status_update":
            return

        if "gcode_move" in data:
            if "homing_origin" in data["gcode_move"]:
                self.labels['zoffset'].set_text("%.2fmm" % data["gcode_move"]["homing_origin"][2])

    def change_babystepping(self, widget, dir):
        if dir == "+":
            gcode = "SET_GCODE_OFFSET Z_ADJUST=%s MOVE=1" % self.bs_delta
        else:
            gcode = "SET_GCODE_OFFSET Z_ADJUST=-%s MOVE=1" % self.bs_delta

        self._screen._ws.klippy.gcode_script(gcode)



    def change_bs_delta(self, widget, bs):
        if self.bs_delta == bs:
            return
        logging.info("### BabyStepping " + str(bs))

        ctx = self.labels[str(self.bs_delta)].get_style_context()
        ctx.remove_class("distbutton_active")

        self.bs_delta = bs
        ctx = self.labels[self.bs_delta].get_style_context()
        ctx.add_class("distbutton_active")
        for i in self.bs_deltas:
            if i == self.bs_delta:
                continue
            self.labels[i].set_active(False)
    
    def Move_Z0(self, widget):
        gcode = "G28\nG1 Z0 F1000"
        self._screen._ws.klippy.gcode_script(gcode)
    