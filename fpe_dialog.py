import os
from qgis.core import QgsMapLayerProxyModel
from qgis.PyQt.QtWidgets import QDialogButtonBox
from qgis.PyQt import uic, QtWidgets


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'fpe_dialog.ui'))


class fpeDialog(QtWidgets.QDialog, FORM_CLASS):
    """ Main plugin dialog class """
    
    def __init__(self, runPlugin, parent=None):
        """ Constructor.  UI dialog initialization """
        super().__init__(parent)  
        self.parent = parent
        self.setupUi(self)
        self.setWindowTitle("French Point Elevation")
        self.qt_cb_selectedLayer.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.qt_cb_selectedLayer.layerChanged.connect(self.layer_infos)
        self.qt_fieldName.textChanged.connect(self.field_infos)
        self.qt_button_box.button(QDialogButtonBox.StandardButton.Ok).clicked.connect(runPlugin)

        txt_intro = ("Ce plugin permet de récupérer l'altitude issu du RGE Alti® à partir du Service Géoplateforme de calcul altimétrique fourni par l'"
                     "<a href=\"https://geoservices.ign.fr/documentation/services/services-geoplateforme/altimetrie\" target=\"_blank\">IGN</a>")
        self.qt_text_intro.setText(txt_intro)

        # Resource list
        self.qt_cb_selectedResource.addItem('ign_rge_alti_par_territoires')
        self.qt_cb_selectedResource.addItem('ign_rge_alti_wld')
        # self.qt_cb_selectedResource.addItem('ALTIMETRIE') #not implemented yet
        # self.qt_cb_selectedResource.addItem('IGNF_LIDARHD_MNX_WLD') #not implemented yet
        
        self.qt_cb_selectedResource.currentTextChanged.connect(self.resource_infos)
        self.qt_progressBar.setValue(0)
        

    def layer_infos(self):
        """ Print message on selected layer's infos """
        layer = self.qt_cb_selectedLayer.currentLayer()
        # Print entities number
        if not layer:
            self.qt_message_selectedLayerInfos.setText(f"")    
        elif layer.featureCount() <=5000:
            self.qt_message_selectedLayerInfos.setText(
                f"<i>La couche sélectionnée contient <b>{layer.featureCount()} points</b></i>"
            )
            self.field_infos()
        elif layer.featureCount() >5000:
            self.qt_message_selectedLayerInfos.setText(
                    f"<p style='color:red; font-style:italic'>Attention, un nombre d'entité trop élevé peut générer une requête très longue<br><b>({layer.featureCount()} points)</b></p>"
                )
            self.field_infos()
            
        # Others update
        self.qt_progressBar.setValue(0) # Reset Progres Bar

    
    def field_infos(self):
        """ Print message if field already exists """
        layer = self.qt_cb_selectedLayer.currentLayer()
        if not layer:
            field_index = 0
        else:
            field_name = self.qt_fieldName.text()
            field_index = layer.fields().indexFromName(field_name)
        if not field_index == -1:
            self.qt_message_fieldName.setText(
                f"<i>Le champ <b>{field_name}</b> existe et sera mis à jour</i>"
            )
        else :
             self.qt_message_fieldName.setText('')
    

    def resource_infos(self):
        """ Print message on selected resource """
        resource = self.qt_cb_selectedResource.currentText()
        if resource == 'ign_rge_alti_par_territoires':
           resource_link = '\"https://data.geopf.fr/altimetrie/resources/ign_rge_alti_par_territoires/\"'
           self.qt_message_resource.setText(f'<i>RGE Alti 1m - France + DOM par territoire - Source et précision dynamiques <a href={resource_link} target=\"_blank\">Détails</a></i>')           
        elif resource == 'ign_rge_alti_wld':
            resource_link = '\"https://data.geopf.fr/altimetrie/resources/ign_rge_alti_wld/\"'
            self.qt_message_resource.setText(f'<i>RGE Alti - France entière - métadonnées statiques <a href={resource_link} target=\"_blank\">Détails</a></i>')
            # https://data.geopf.fr/altimetrie/resources/ign_rge_alti_wld/
        # elif resource == 'ALTIMETRIE':
        #     self.qt_message_resource.setText(f'<i>LidarHD : MNT et MNS, à 50 cm</i>')
        #     # https://data.geopf.fr/altimetrie/resources/ALTIMETRIE/
        # elif resource == 'IGNF_LIDARHD_MNX_WLD':
        #     self.qt_message_resource.setText(f'<i>LIDAR HD - France entière - produit dérivées MNT, MNS et MNH</i>')
        #     # https://data.geopf.fr/altimetrie/resources/IGNF_LIDARHD_MNX_WLD/