from qgis.core import Qgis, QgsVectorDataProvider, QgsField, edit, QgsCoordinateReferenceSystem
from qgis.utils import iface
from qgis.gui import QgsMapToolEmitPoint
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.PyQt.QtGui import QIcon
from PyQt5.QtCore import *
from PyQt5.Qt import QApplication
from .fpe_utils import item_path, CrsTransform, ApiUrl
from .fpe_dialog import fpeDialog
import re
import json
import requests


PLUGIN_NAME = 'French Point Elevation'

class FrenchPointElevation:
    """ Main class """

    def __init__(self, iface):
        """ Constructor """

        self.iface = iface
        self.action = None

        # For second button "actionGetElevOnClick"
        self.canvas = self.iface.mapCanvas()
        self.point_tool = QgsMapToolEmitPoint(self.canvas)
        

    def initGui(self):
        """ Create the menu entries and toolbar icons inside the QGIS GUI """

        fpe_icon_point = item_path('fpe_icon_onpoint.png')
        fpe_icon_onClick = item_path('fpe_icon_onclick.png')

        self.pluginMenu = iface.pluginMenu().addMenu( QIcon(str(fpe_icon_point)), PLUGIN_NAME )
        self.toolBarButtons = [] ## Liste des QAction (boutons) à ajouter à la bar d'outils du plugin
        
        # Get Elevation from a point Layer. Fist process
        self.actionGetElevOnPoint = QAction(QIcon(str(fpe_icon_point)), "Récupérer l'altitude d'une couche de point", self.iface.mainWindow())
        self.actionGetElevOnPoint.triggered.connect(self.run_GetElevOnPoint)
        self.pluginMenu.addAction(self.actionGetElevOnPoint)
        self.toolBarButtons.append(self.actionGetElevOnPoint)

        # Get Elevation from click on canvas. Second process
        self.actionGetElevOnClick = QAction(QIcon(str(fpe_icon_onClick)), "Récupérer l'altitude à la volée", self.iface.mainWindow())
        self.actionGetElevOnClick.triggered.connect(self.run_GetElevOnClick)
        self.pluginMenu.addAction(self.actionGetElevOnClick)
        self.toolBarButtons.append(self.actionGetElevOnClick)
        self.first_start = True # To not have several opening windows on successives actions
        
        self.toolBar = iface.addToolBar(PLUGIN_NAME)
        for action in self.toolBarButtons:  self.toolBar.addAction(action)

 
    def unload(self):
        """ Removes the plugin menu item and icon from QGIS GUI """
        self.pluginMenu.parentWidget().removeAction(self.pluginMenu.menuAction()) # Remove from Extension menu
        self.iface.removeToolBarIcon(self.pluginMenu.menuAction())
        del self.action


    def run_GetElevOnPoint(self):
        """ Call the dialog for the plugin's fisrt process """
        self.dlg = fpeDialog(self.apiRequest) # Called function when press OK button
        self.dlg.show() # show the dialog
    

    def CheckisValidInputLayer(self):
        """ Input validation """
        layer = self.dlg.qt_cb_selectedLayer.currentLayer()
        if not layer:
            QMessageBox.information(None, PLUGIN_NAME, "Aucune couche. Arrêt du script")
            return False
        # Check if Edit mode is closed
        if layer.isEditable() is True:
            QMessageBox.information(None, PLUGIN_NAME, "La couche est en cours d'edition. Arrêt du script")
            return False
        # Check if at least one object
        if layer.featureCount() == 0:
            QMessageBox.information(None, PLUGIN_NAME, "La couche est vide. Arrêt du script")
            return False
        # Check if non editable layer
        if layer.startEditing() is False:
            QMessageBox.information(None, PLUGIN_NAME, "Couche non editable. Arrêt du script")
            return False
        else:
            layer.commitChanges()
        return layer


    def apiRequest(self):
        """ Get the layer informations, build the API request with selected API resource and return the Z values on each entities. Then, update input layer's field """
        # Check if layer is valid
        if self.CheckisValidInputLayer() is False:
            return
        else :
            vlayer = self.CheckisValidInputLayer()
        
        # Form parameters
        field_name = self.dlg.qt_fieldName.text()
        resource_name = self.dlg.qt_cb_selectedResource.currentText()

        # CRS Transform to EPSG:4326 needed for API's input
        crsSrc = QgsCoordinateReferenceSystem(vlayer.crs().authid())
        crsTransform = CrsTransform(crsSrc, 'EPSG:4326')
        
        # Prepare list for API's input
        lons = []
        lats = []
        features = vlayer.getFeatures()
        for feature in features:
            pt = crsTransform.transform(feature.geometry().asPoint()) # Transform crs of each entity
            # List append with seprator
            lons.append(str(pt.x()) + '|')
            lats.append(str(pt.y()) + '|')
        
        # Variables initialization
        nb_features = len(lons) # Evaluate the entities number
        compteur = 0 # Start count of the progress bar
        z_list = [] # List with the elevation values returned by the API
        
        # Loop with 100 features max
        for i in range(0, nb_features, 100):
            # Convert list with a Regular expression in the url's input format
            x = re.sub(r"[,' ]+", "", str(lons[i:i+100]))
            y = re.sub(r"[,' ]+", "", str(lats[i:i+100]))
            # Supprime le 1er et les 2 derniers caractères
            a = x[1:-2]
            b = y[1:-2]
            # print(ApiUrl(a,b, resource_name, 'false', 'true'))
            try:
                url = ApiUrl(a, b, resource_name, 'true', 'true')
                response = requests.get(url)
                datas = json.loads(response.text)
            except Exception: # If API is not working
                QMessageBox.information(None,  PLUGIN_NAME, 'Erreur API : la requête a échoué')
                return
            # Append z_list with the elevation values and progtress bar
            for data in datas["elevations"]:
                # z_list.append(data["z"])
                z_list.append(data)
                compteur += 1
                progession_percent = compteur * 100 / nb_features
                self.dlg.qt_progressBar.setValue(int(progession_percent))
        
        # Call provider
        caps = vlayer.dataProvider().capabilities()

        # Delete field if exists
        field_index = vlayer.fields().indexFromName(field_name)
        if field_index >= 0 : # Because if not exists value == -1
            vlayer.dataProvider().deleteAttributes([field_index])
            vlayer.updateFields()

        # Creeate field
        if caps & QgsVectorDataProvider.AddAttributes:
            vlayer.dataProvider().addAttributes([QgsField(field_name, QVariant.Double)])
        
        # Update attribute
        with edit(vlayer):
            for i, feature in enumerate(vlayer.getFeatures()):
                feature[field_name] = z_list[i]
                vlayer.updateFeature(feature)
        vlayer.updateFields() # Update table
        
        #Finish message
        self.iface.messageBar().clearWidgets()
        self.iface.messageBar().pushMessage(PLUGIN_NAME, 'Ok ' + str(nb_features) + " valeurs ont été récupérées",level=Qgis.Success, duration=7)
        self.dlg.close()

    
    def run_GetElevOnClick(self):
        """ Create signal for the plugin's second process """
        if self.first_start == True:
            self.first_start = False
            self.point_tool.canvasClicked.connect(self.display_point)
        self.canvas.setMapTool(self.point_tool)


    def display_point(self, point):
        """ Get XY from canvas, build API's url and return the Z values of the clicked point using the ign_rge_ali_wld resource because it is the most available datas.
        Then, display results in a QGIS message box and copy XYZ values when user closed the box """
        try :
            # CRS Transform to EPSG:4326 needed for API's input
            sourceCrs = QgsCoordinateReferenceSystem(iface.mapCanvas().mapSettings().destinationCrs().authid())
            crsTransform = CrsTransform(sourceCrs, 'EPSG:4326')
            pt = crsTransform.transform(point)
            try:
                # ign_rge_alti_par_territoires
                # ALTIMETRIE
                url = ApiUrl(str(pt.x()), str(pt.y()), 'ign_rge_alti_wld', 'true', 'true')
                response = requests.get(url)
                datas = json.loads(response.text)
            except Exception: # If API is not working
                QMessageBox.information(None, PLUGIN_NAME, 'Erreur API : la requête a échoué')
                return
            x = point.x()
            y = point.y()
            z = datas["elevations"][0]
            coords = f'x : {x}, y : {y}, z = {z}'
            QMessageBox.information(None, PLUGIN_NAME, f'{coords} <br> Ressource = ign_rge_alti_wld')
            clipboard = QApplication.clipboard()
            clipboard.setText(str(x) + ' ' + str(y) + ' ' + str(z))
            self.iface.messageBar().clearWidgets()
            self.iface.messageBar().pushMessage(PLUGIN_NAME," Données copiées. Utiliser Ctrl+V pour coller les valeurs XYZ (CRS du projet, séparateur = espace)",level=Qgis.Success, duration=7)
        except Exception:
            QMessageBox.information(None, PLUGIN_NAME, 'Erreur')
            return
