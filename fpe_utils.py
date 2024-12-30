from qgis.core import QgsProject, QgsVectorLayer, QgsCoordinateReferenceSystem, QgsCoordinateTransform
from pathlib import Path


def item_path(*args) -> Path:
    """Return the path to the plugin item's arg"""
    path = Path(__file__).resolve().parent
    for item in args:
        path = path.joinpath(item)
    return path

def isValidLayer(x):
    # Editable, mode edition fermé
    if type(x) == QgsVectorLayer:
        return True
    return False

# Feature crs tranform. Use it with : .transform(feature.geometry().asPoint())
def CrsTransform(crsSrc,crsDest):
    crsSrc = QgsCoordinateReferenceSystem(crsSrc)    # Input layer's CRS
    crsDest = QgsCoordinateReferenceSystem(crsDest)  # WGS 84 / UTM zone 33N
    transformContext = QgsProject.instance().transformContext()
    xform = QgsCoordinateTransform(crsSrc, crsDest, transformContext)
    return xform

# build API's url
def ApiUrl(x, y, resource_arg, zonly_arg, indent_arg):
    resource = resource_arg
    zonly = zonly_arg
    indent = indent_arg
    url = 'https://data.geopf.fr/altimetrie/1.0/calcul/alti/rest/elevation.json?resource=' + resource + '&lon=' + x + '&lat=' + y + '&zonly=' + zonly + '&indent=' + indent
    return url
