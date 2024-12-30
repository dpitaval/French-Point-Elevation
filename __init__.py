"""
/***************************************************************************
 French Point Elevation
                                 A QGIS plugin
This plugin use the IGN's REST API to download elevation on an existing layer (point only) or directly by clicking on the map.
The values comes from the RGE Alti® database provides by IGN. 
It was created from the minimal_plugin's base.
                             -------------------
        begin                : 2024-05-20
        copyright            : (C) 2024 by David Pitaval
        email                : d.pitaval@groupeginger.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""

def classFactory(iface):
    from .fpe_main import FrenchPointElevation
    return FrenchPointElevation(iface)