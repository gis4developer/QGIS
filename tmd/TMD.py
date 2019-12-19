# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TMD
                                 A QGIS plugin
 Get Weather Today from v2.00
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2019-12-12
        git sha              : $Format:%H$
        copyright            : (C) 2019 by GIS4Dev
        email                : gis4developer@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QThread, pyqtSignal
from qgis.PyQt.QtGui import QIcon, QWindow
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMainWindow
from qgis.core import QgsGeometry, QgsPointXY, QgsFeature, QgsVectorLayer, QgsProject, Qgis
# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .TMD_dialog import TMDDialog
import os.path
import requests
import xml.etree.ElementTree as ET

class CloneThread(QThread):
    signal = pyqtSignal('PyQt_PyObject')
    def __init__(self):
        QThread.__init__(self)
        self.git_url = ""

    def run(self):
        url = "http://data.tmd.go.th/api/WeatherToday/V2/?uid=api&ukey=api12345"
        r = requests.get(url)

        if r.status_code == requests.codes.ok and r.headers['Content-Type'] == "text/xml; charset=utf-8":
            root = ET.fromstring(r.text.encode('utf-8'))
            Stations = root[1]

            uri = "Point?crs=epsg:4326&field=WmoStationNumber:integer&field=StationNameThai:string(254)&field=StationNameEnglish:string(254)\
            &field=Province:string(254)&field=date:date&field=time:string(5)&field=MeanSeaLevelPressure:double&field=MeanSeaLevelPressure_Unit:string(8)\
            &field=temperature:double&field=temperature_unit:string(8)&field=maxTemperature:double&field=maxTemperature_unit:string(8)\
            &field=DifferentFromMaxTemperature:double&field=DifferentFromMaxTemperature_unit:string(8)&field=MinTemperature:double&field=MinTemperature_unit:string(8)\
            &field=DifferentFromMinTemperature:double&field=DifferentFromMinTemperature_unit:string(8)&field=RelativeHumidity:double&field=RelativeHumidity_unit:string(8)\
            &field=WindDirection:double&field=WindDirection_unit:string(8)&field=WindSpeed:double&field=WindSpeed_unit:string(8)\
            &field=Rainfall:double&field=Rainfall_unit:string(8)&index=yes"

            vl = QgsVectorLayer(uri, "temporary_points", "memory")
            pr = vl.dataProvider()
            vl.updateFields()
            total = len(Stations)
            count = 1

            for station in Stations:
                lng = station.find('Longitude').text
                lat = station.find('Latitude').text
                wmoStationNumber = station.find('WmoStationNumber').text
                stationNameThai = station.find('StationNameThai').text
                stationNameEnglish = station.find('StationNameEnglish').text
                province = station.find('Province').text

                #---------- Observation ----------#
                Observation = station.find('Observation')
                date = Observation.find('DateTime').text.split(" ")[0]
                time = Observation.find('DateTime').text.split(" ")[1]
                meanSeaLevelPressure = Observation.find('MeanSeaLevelPressure').text
                meanSeaLevelPressure_unit = Observation.find('MeanSeaLevelPressure').attrib['unit']
                temperature = Observation.find('Temperature').text
                temperature_unit = Observation.find('Temperature').attrib['Unit']
                maxTemperature = Observation.find('MaxTemperature').text
                maxTemperature_unit = Observation.find('MaxTemperature').attrib['Unit']
                differentFromMaxTemperature = Observation.find('DifferentFromMaxTemperature').text
                differentFromMaxTemperature_unit = Observation.find('DifferentFromMaxTemperature').attrib['Unit']
                minTemperature = Observation.find('MinTemperature').text
                minTemperature_unit = Observation.find('MinTemperature').attrib['Unit']
                differentFromMinTemperature = Observation.find('DifferentFromMinTemperature').text
                differentFromMinTemperature_unit = Observation.find('DifferentFromMinTemperature').attrib['Unit']
                relativeHumidity = Observation.find('RelativeHumidity').text
                relativeHumidity_unit = Observation.find('RelativeHumidity').attrib['Unit']
                windDirection = Observation.find('WindDirection').text
                windDirection_unit = Observation.find('WindDirection').attrib['Unit']
                windSpeed = Observation.find('WindSpeed').text
                windSpeed_unit = Observation.find('WindSpeed').attrib['Unit']
                rainfall = Observation.find('Rainfall').text
                rainfall_unit = Observation.find('Rainfall').attrib['Unit']

                fet = QgsFeature()
                fet.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(float(lng),float(lat))))
                fet.setAttributes([
                    wmoStationNumber, 
                    stationNameThai, 
                    stationNameEnglish,
                    province,
                    date,
                    time,
                    meanSeaLevelPressure, meanSeaLevelPressure_unit,
                    temperature, temperature_unit,
                    maxTemperature, maxTemperature_unit,
                    differentFromMaxTemperature, differentFromMaxTemperature_unit,
                    minTemperature, minTemperature_unit,
                    differentFromMinTemperature, differentFromMinTemperature_unit,
                    relativeHumidity, relativeHumidity_unit,
                    windDirection, windDirection_unit,
                    windSpeed, windSpeed_unit,
                    rainfall, rainfall_unit
                ])
                pr.addFeatures([fet])

                count = count +1

                self.signal.emit( (count/total)*100 )

            vl.updateExtents()
            self.signal.emit(vl)

        else:
            #cannot load data from TMD, May be TMD down or internet connection down.
            self.signal.emit(500)


class TMD:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'TMD_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Thai Meteorological Department (TMD)')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('TMD', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToWebMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/TMD/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Thai Meteorological Department (TMD)'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginWebMenu(
                self.tr(u'&Thai Meteorological Department (TMD)'),
                action)
            self.iface.removeToolBarIcon(action)

    def finished(self, result):
        if result == 500: #Error
            self.iface.messageBar().pushMessage("Please check the internet connection.", level=Qgis.Info, duration=3)
            self.dlg.close()
        elif type(result) is int or type(result) is float:
            self.dlg.label.setText("Receiving data...")
            self.dlg.progressBar.setValue(int(result))
        else:
            QgsProject.instance().addMapLayer(result)
            self.dlg.close()
            self.dlg.progressBar.setValue(0)
            self.iface.messageBar().pushMessage("Added layer successfully.", level=Qgis.Success, duration=3)

    def run(self):
        """Run method that performs all the real work"""

        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = TMDDialog()
            self.dlg.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)

        self.dlg.show()

        self.git_thread = CloneThread()  # This is the thread object
        # Connect the signal from the thread to the finished method
        self.git_thread.signal.connect(self.finished)
        self.git_thread.start()

