# -*- coding: utf-8 -*-
"""
Created on Thu Sep 21 14:19:57 2017

@author: c1649794
"""
#System Imports
import sys, os
#PyQt Imports
from PyQt4.QtCore import *
from PyQt4.QtGui import *
#Matplotlib Imports
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec
#Numpy Imports
import numpy as np
#Astropy Imports
from astropy.io import fits
from astropy.wcs import WCS

class AppForm(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle('PPPlot')
        self.create_status_bar()
        self.imHere = False

        if len(sys.argv) > 1:
            self.fname = sys.argv[1]
            if os.path.exists(self.fname) is False:
                print 'ERROR: Path does not exist.'
                exit
            self.loading()
        else:
            self.load_plot()

    def load_plot(self):
        path = str(QFileDialog.getOpenFileName(self,'Open File'))
        self.fname = unicode(path, encoding='UTF-8')
        self.loading()

    def save_plot(self):
        file_choices = "PNG (*.png)|*.png"

        path = unicode(QFileDialog.getSaveFileName(self,
                        'Save file', '',
                        file_choices))
        if path:
            self.canvas.print_figure(path, dpi=self.dpi)
            self.statusBar().showMessage('Saved to %s' % path, 2000)

    def on_about(self):
        msg = """
PPPlot: A tool for plotting PPMAP image cubes

Version 0.1

On Canvas
* Show Grid: (Toggle) Display a celestial grid over the image
* Auto-Scale: (Toggle) Allow PPPlot to set brightness cuts automatically for each slice
* Min | Max: (Write) Define custom brightness thresholds (default to 0% to 99% scaling)
* Temperature: (Slider) Change current temperature slice
* Opacity: (Slider, Optional) Change current opacity index slice (only on plots with more than one beta value)

Edit Menu
* Colour: Select color maps (default matplotlib plasma)

If you encounter any problems when using PPPlot, please direct any questions or bug reports to:

Alexander.Howard@astro.cf.ac.uk
        """

    def loading(self):
        self.hdu = fits.open(self.fname)[0]
        self.hdr = self.hdu.header
        if float(self.hdr['CDELT4']) == float(0.0):
            self.fixBeta = self.hdr['CRVAL4']
            self.hdr['NAXIS'] = 3
            self.hdr.remove('NAXIS4')
            self.hdr.remove('CRPIX4')
            self.hdr.remove('CRVAL4')
            self.hdr.remove('CDELT4')
            self.hdu.data = self.hdu.data[0,:,:,:]
            self.im = self.hdu.data
            self.wcs = WCS(self.hdr).celestial
            valVmax = str(np.nanmax(self.hdu.data[int(self.hdr['NAXIS3']/2)-1,:,:]) * 0.99)
            valVmin = str(np.nanmax(self.hdu.data[int(self.hdr['NAXIS3']/2)-1,:,:]) * 0.00)
        else:
            self.im = self.hdu.data
            self.wcs = WCS(self.hdr).celestial
            valVmax = str(np.nanmax(self.hdu.data[int(self.hdr['NAXIS4']/2)-1,int(self.hdr['NAXIS3']/2)-1,:,:]) * 0.99)
            valVmin = str(np.nanmax(self.hdu.data[int(self.hdr['NAXIS4']/2)-1,int(self.hdr['NAXIS3']/2)-1,:,:]) * 0.00)
        self.xMinLimDefault , self.xMaxLimDefault = (0, self.hdr['NAXIS1'])
        self.yMinLimDefault , self.yMaxLimDefault = (0, self.hdr['NAXIS2'])
        self.create_menu()
        self.create_main_frame()
        self.status_text.setText(self.fname)
        self.cmapName = 'plasma'
        self.vmaxBox.setText(valVmax)
        self.vminBox.setText(valVmin)
        self.on_draw()

    def on_draw(self):
        """ Redraws the figure
        """
        fontfamily = 'serif'
        gridColour = 'white'

        if self.imHere:
            self.on_xlims_change()
            self.on_ylims_change()
        else:
            self.xMinLimit, self.xMaxLimit = (self.xMinLimDefault, self.xMaxLimDefault)
            self.yMinLimit, self.yMaxLimit = (self.yMinLimDefault, self.yMaxLimDefault)

        # clear the axes and redraw the plot anew
        #
        self.axes.clear()
        if self.grid_cb.isChecked():
            self.axes.grid(True, color = gridColour, alpha = 0.5)
        else:
            self.axes.grid(True, color = None, alpha = 0.0)

        self.cax.clear()


        tempSlice = self.tempSlider.value() -1
        temp = '{:3.1f} K'.format(10.**(self.hdr['CRVAL3'] + (tempSlice * self.hdr['CDELT3'])))
        self.tempBox.setText(temp)

        if (self.autoScale.isChecked()):
            Vmax = None
            Vmin = None
        else:
            Vmax = float(self.vmaxBox.text())
            Vmin = float(self.vminBox.text())

        if self.hdr['NAXIS'] > 3:
            betaSlice = self.betaSlider.value() -1
            betchar = u"\u03B2"
            beta = betchar + ' {:3.1f}'.format(self.hdr['CRVAL4'] + (betaSlice * self.hdr['CDELT4']))
            self.betaBox.setText(beta)

            img = self.axes.imshow(self.im[betaSlice,tempSlice,:,:], origin = 'lower',
                                   vmin = Vmin, vmax = Vmax, cmap = self.cmapName,
                                   interpolation = 'none')#, extent = (self.xMinLimit, self.xMaxLimit, self.yMinLimit, self.yMaxLimit))
        else:
            img = self.axes.imshow(self.im[tempSlice,:,:], origin = 'lower',
                                   vmin = Vmin, vmax = Vmax, cmap = self.cmapName,
                                   interpolation = 'none')#, extent = (15, 30, 15, 30))

        self.imHere = True


        cbar = self.fig.colorbar(img, self.cax)

        RA = self.axes.coords[0]
        DEC = self.axes.coords[1]

        RA.set_axislabel('RA (J2000)', family = fontfamily, minpad=0.8)
        DEC.set_axislabel('Dec (J2000)', family = fontfamily, minpad=-0.4)

        RA.set_major_formatter('hh:mm:ss.s')
        RA.set_separator(('h','m','s'))
        RA.set_ticklabel(family = fontfamily)
        RA.set_ticks(color = gridColour)
        DEC.set_major_formatter('dd:mm:ss')
        DEC.set_ticklabel(family = fontfamily)
        DEC.set_ticks(color = gridColour)

        cbar.set_label('Dif. Col. Den. ($10^{20}$ g cm$^{-2}$)', family = fontfamily)
        for l in cbar.ax.yaxis.get_ticklabels():
            l.set_family(fontfamily)

        vminText, vmaxText = img.get_clim()
        self.vmaxBox.setText('{:5.1f}'.format(vmaxText))
        self.vminBox.setText('{:5.1f}'.format(vminText))

        self.axes.set_xlim(xmin=self.xMinLimit,xmax=self.xMaxLimit)
        self.axes.set_ylim(ymin=self.yMinLimit,ymax=self.yMaxLimit)

        self.canvas.draw()

#        self.axes.callbacks.connect('xlim_changed', self.on_xlims_change)
#        self.axes.callbacks.connect('ylim_changed', self.on_ylims_change)

    def create_main_frame(self):
        self.main_frame = QWidget()

        # Create the mpl Figure and FigCanvas objects.
        # 5x4 inches, 100 dots-per-inch
        #
        self.dpi = 100
        self.fig = Figure((10.0, 10.0), dpi=self.dpi)
        self.gs = gridspec.GridSpec(1, 2, width_ratios=[15,1])
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)

        # Since we have only one plot, we can use add_axes
        # instead of add_subplot, but then the subplot
        # configuration tool in the navigation toolbar wouldn't
        # work.
        #

        self.axes = self.fig.add_subplot(self.gs[0],projection = self.wcs)
        self.cax = self.fig.add_subplot(self.gs[1])

        # Create the navigation toolbar, tied to the canvas
        #
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)

        # Other GUI elements

        self.grid_cb = QCheckBox("Show &Grid")
        self.grid_cb.setChecked(False)
        self.connect(self.grid_cb, SIGNAL('stateChanged(int)'), self.on_draw)

        self.autoScale = QCheckBox("Auto &Scale")
        self.autoScale.setChecked(False)
        self.connect(self.autoScale, SIGNAL('stateChanged(int)'), self.on_draw)

        tempSlider_label = QLabel('Temperature')
        self.tempSlider = QSlider(Qt.Horizontal)
        self.tempSlider.setRange(1, self.hdr['NAXIS3'])
        self.tempSlider.setValue(int(self.hdr['NAXIS3']/2))
        self.tempSlider.setTracking(True)
        self.tempSlider.setTickPosition(QSlider.TicksBothSides)
        self.connect(self.tempSlider, SIGNAL('valueChanged(int)'), self.on_draw)
        self.tempBox = QLabel()

        self.vLabel = QLabel()
        self.vLabel.setText('Min | Max')

        self.vminBox = QLineEdit()
        self.vminBox.setMinimumWidth(75)
        self.vminBox.setMaximumWidth(75)
        self.connect(self.vminBox, SIGNAL('editingFinished ()'), self.on_draw)

        self.vmaxBox = QLineEdit()
        self.vmaxBox.setMinimumWidth(75)
        self.vmaxBox.setMaximumWidth(75)
        self.connect(self.vmaxBox, SIGNAL('editingFinished ()'), self.on_draw)


        self.hBlank = QSpacerItem(75,1)
        self.iBlank = QSpacerItem(75,1)
        self.vBlank = QSpacerItem(1,25)

        #
        # Layout with box sizers
        #
        hbox = QGridLayout()
        hbox.addItem(self.hBlank, 0, 0, 3, 1)
        hbox.addWidget(self.grid_cb, 0, 1, 1, 1)
        hbox.addWidget(self.autoScale, 0, 2, 1, 1)
        hbox.addWidget(self.vLabel,0,3,1,1, Qt.AlignRight)
        hbox.addWidget(self.vminBox,0 ,4, 1, 1)
        hbox.addWidget(self.vmaxBox,0,5,1,1)
        hbox.addItem(self.iBlank,0,6,3,1)
        hbox.addWidget(tempSlider_label, 1, 1, 1, 1)
        hbox.addWidget(self.tempSlider, 1, 2, 1, 3)
        hbox.addWidget(self.tempBox, 1, 5, 1, 1)

        if self.hdr['NAXIS'] > 3:
            betaSlider_label = QLabel('Opacity Index')
            self.betaSlider = QSlider(Qt.Horizontal)
            self.betaSlider.setRange(1, self.hdr['NAXIS4'])
            self.betaSlider.setValue(int(self.hdr['NAXIS4']/2))
            self.betaSlider.setTracking(True)
            self.betaSlider.setTickPosition(QSlider.TicksBothSides)
            self.connect(self.betaSlider, SIGNAL('valueChanged(int)'), self.on_draw)
            self.betaBox = QLabel()

            hbox.addWidget(betaSlider_label, 2, 1, 1, 1)
            hbox.addWidget(self.betaSlider, 2, 2, 1, 3)
            hbox.addWidget(self.betaBox, 2, 5, 1, 1)
        else:
            betaSlider_label = QLabel('Fixed Opac. In.')
            self.betaBox = QLabel()
            self.betaBox.setText(' {:3.1f}'.format(self.fixBeta))
            hbox.addWidget(betaSlider_label, 2, 1, 1, 1)
            hbox.addWidget(self.betaBox, 2, 2, 1, 1)

        hbox.addItem(self.vBlank,3,3,1,1)

        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        vbox.addLayout(hbox)

        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)

    def create_status_bar(self):
        self.status_text = QLabel("PPMAP Temperature/Beta Cube Plotter")
        self.statusBar().addWidget(self.status_text, 1)

    def create_menu(self):
        self.file_menu = self.menuBar().addMenu("&File")

        load_file_action = self.create_action('&Load Cube',
            shortcut='Ctrl+O', slot=self.load_plot,
            tip='Load a cube')
        save_file_action = self.create_action("&Save plot",
            shortcut="Ctrl+S", slot=self.save_plot,
            tip="Save the plot")
        quit_action = self.create_action("&Quit", slot=self.close,
            shortcut="Ctrl+Q", tip="Close the application")

        self.add_actions(self.file_menu,
            (load_file_action, save_file_action, None, quit_action))

        self.edit_menu = self.menuBar().addMenu("&Edit")

        self.pick_color_action = self.edit_menu.addMenu("&Colour Map")

        plasma_map = self.create_action("&Plasma (default)", devStr = 'plasma')
        jet_map = self.create_action("&Jet", devStr = 'jet')
        rainbow_map = self.create_action("&Rainbow", devStr = 'rainbow')
        viridis_map = self.create_action("&Viridis", devStr = 'viridis')
        blue_map = self.create_action("&Blue", devStr = 'Blues')
        green_map = self.create_action("&Green", devStr = 'Greens')
        red_map = self.create_action("&Red", devStr = 'Reds')
        gray_map = self.create_action("&Gray", devStr = 'gray')

        self.add_actions(self.pick_color_action, (plasma_map, None, jet_map,
            rainbow_map, viridis_map, None, blue_map, green_map, red_map, gray_map))
        self.pick_color_action.triggered[QAction].connect(self.on_color)

        self.help_menu = self.menuBar().addMenu("&Help")
        about_action = self.create_action("&About",
            shortcut='F1', slot=self.on_about,
            tip='About PPPlot')

        self.add_actions(self.help_menu, (about_action,))

    def on_color(self,q):
        self.cmapName = q.data()
        self.on_draw()

    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def create_action(  self, text, slot=None, shortcut=None,
                        icon=None, tip=None, checkable=False,
                        signal="triggered()", devStr=None):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        if devStr is not None:
            action.setData(devStr)
        return action

    def on_xlims_change(self):
        self.xMinLimit, self.xMaxLimit = self.axes.get_xlim()
    def on_ylims_change(self):
        self.yMinLimit, self.yMaxLimit = self.axes.get_ylim()

def main():
    global app
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    form = AppForm()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()