# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QuickStepGeobia
                                 A QGIS plugin
 Accuracy assessment of object-based image classification - GEOBIA
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-03-06
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Salomón Einstein, Ivan Lizarazo
        email                : seramirezf@correo.udistrital.edu.co, ializarazos@unal.edu.co
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
from os import path, chdir
from pathlib import Path
from copy import deepcopy
from math import sqrt, pi
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QFileDialog
from qgis.gui import QgsMapToolEmitPoint, QgsMapLayerComboBox, QgsFieldComboBox
from qgis.core import QgsGeometry, QgsMapLayerProxyModel, QgsFieldProxyModel

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .quickstepgeobia_dialog import QuickStepGeobiaDialog
import os.path


class QuickStepGeobia:
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
            'QuickStepGeobia_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Quick STEP GEOBIA')

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
        return QCoreApplication.translate('QuickStepGeobia', message)


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
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/quickstepgeobia/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Similarity matrix for GEOBIA accuracy'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Quick STEP GEOBIA'),
                action)
            self.iface.removeToolBarIcon(action)


    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = QuickStepGeobiaDialog()

        # show the dialog
        self.dlg.show()
        self.dlg.cboRefObjLyr.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.dlg.cboClaObjLyr.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.dlg.cboRefObjFld.setFilters(QgsFieldProxyModel.String)
        self.dlg.cboClaObjFld.setFilters(QgsFieldProxyModel.String)
        
        #slots and signals
        self.loadFields()
        self.dlg.cboRefObjLyr.layerChanged.connect(self.loadFields)
        self.dlg.cboClaObjLyr.layerChanged.connect(self.loadFields)
        self.dlg.btnAssess.clicked.connect(self.assessAccuracy)
        self.dlg.btnFindPath.clicked.connect(self.chooseDirectory)
        self.dlg.btnClear.clicked.connect(self.clearDialog)
        self.dlg.btnExit.clicked.connect(self.closeDialog)
      
        
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass


    def loadFields(self):
        """Load fields from seleted layer"""
        refObjLyr = self.dlg.cboRefObjLyr.currentLayer()
        claObjLyr = self.dlg.cboClaObjLyr.currentLayer()
        self.dlg.cboRefObjFld.setLayer(refObjLyr)
        self.dlg.cboClaObjFld.setLayer(claObjLyr)
        

    def chooseDirectory(self):
        """ """
        dirName = QFileDialog.getExistingDirectory(self.dlg, "Select directory")
        self.dlg.txtDirName.setText(dirName)

    
    def clearDialog(self):
        """Restore the GUI"""     
        self.dlg.txtDirName.clear()
        self.dlg.txtResults.clear()
        self.dlg.txtEpsilon.clear()
        self.dlg.progressBar.setValue(0)

        
    def closeDialog(self):
        "Close dialog"
        self.dlg.close()

    
    def isfloat(self, value):
        "Check for float"
        try:
            float(value)
            return True
        except:
            return False
        
	
    def assessAccuracy(self):
        self.dlg.txtResults.clear()
        refObjLyr = self.dlg.cboRefObjLyr.currentLayer()
        claObjLyr = self.dlg.cboClaObjLyr.currentLayer()
        refObjFld = self.dlg.cboRefObjFld.currentField()
        claObjFld = self.dlg.cboClaObjFld.currentField()
 
        if refObjLyr == None and claObjLyr == None:
            QMessageBox.critical(None, "Error", "There are not layers in QGIS. Please add Layers!")
        elif refObjLyr == '' or claObjLyr == '':
            QMessageBox.critical(None, "Error", "Please select both layers")
        elif refObjLyr == claObjLyr:
            QMessageBox.critical(None, "Error", "Reference objects and classified objects are the same!")
        elif refObjFld == '' or claObjFld == '':
            QMessageBox.critical(None, "Error", "Please select category fields")
        elif self.dlg.txtEpsilon.text() == '':
            QMessageBox.critical(None, "Error", "Please enter an allowable horizontal error value!")
        elif self.dlg.txtDirName.text() == '':
            QMessageBox.critical(None, "Error", "Please select results output directory")
        elif self.isfloat(self.dlg.txtEpsilon.text()) == False:
            QMessageBox.critical(None, "Error", "The allowable horizontal error value must be numeric")
        else:
            epsilon = float(self.dlg.txtEpsilon.text())

            #Objects' number
            nRef = refObjLyr.featureCount()
            nCla = claObjLyr.featureCount()

            #calculation of intersection matrix
            mint = []
            for i in list(range(nRef)):
                mint.append([])
                for j in list(range(nCla)):
                    mint[i].append(None)

            for i in refObjLyr.getFeatures():
                for j in claObjLyr.getFeatures():
                    mint[i.id()][j.id()] = i.geometry().intersects(j.geometry())

            #calculation of intersected area matrix
            amint = deepcopy(mint)
            for i in refObjLyr.getFeatures():
                for j in claObjLyr.getFeatures():
                    if mint[i.id()][j.id()] == True:
                        geom = i.geometry().intersection(j.geometry())
                        amint[i.id()][j.id()] = geom.area()
                    else:
                        amint[i.id()][j.id()] = 0

            #Categories' labels
            lblRef = [r[refObjFld] for r in refObjLyr.getFeatures()]
            valRef = list(set(lblRef))
            valRef.sort()

            lblCla = [c[claObjFld] for c in claObjLyr.getFeatures()]
            valCla = list(set(lblCla))
            valCla.sort()

            rdim = len(valRef)
            cdim = len(mint)

            aref = [r.geometry().area() for r in refObjLyr.getFeatures()]
            asum = sum(aref)
            ppref = [p/asum for p in aref]
            wref = [1/w for w in ppref]
            wsum = sum(wref)
            weight = [w/wsum for w in wref]

            # Weights' vertical aggregation
            vrtWeights = []
            for i, v in enumerate(valRef):
                    tmp = 0
                    for j, l in enumerate(lblRef):
                        if v == l:
                            tmp = tmp + weight[j]
                    vrtWeights.append(tmp)

            """Calculation of Theme similarity"""

            #Objects' theme matrix
            theme = deepcopy(mint)
            for i in refObjLyr.getFeatures():
                for j in claObjLyr.getFeatures():
                    if mint[i.id()][j.id()]==True and i[refObjFld]==j[claObjFld]:
                        geom = i.geometry().intersection(j.geometry())
                        theme[i.id()][j.id()] = geom.area() / i.geometry().area()
                    else:
                        theme[i.id()][j.id()] = 0
            
            #Horizontal aggregation
            wtheme = [list(range(rdim)) for i in list(range(cdim))]
            for r in list(range(cdim)):
                for c, v in enumerate(valCla):
                    tmp = 0
                    for j, l in enumerate(lblCla):
                        if v == l:
                            tmp = tmp + amint[r][j] / aref[r]
                    wtheme[r][c] = tmp                    
                    

            #Vertical aggregation
            ttheme = deepcopy(wtheme)
            for i in list(range(cdim)):
                for j in list(range(rdim)):
                     ttheme[i][j] = wtheme[i][j] * weight[i]

            wntheme = [list(range(rdim)) for i in list(range(rdim))]
            for col, lblC in enumerate(valCla):
                pattern = []
                for row, lblR in enumerate(lblRef):
                    pattern.append(lblR + lblC)
                patternVal = list(set(pattern))
                patternVal.sort()
                for i,val in enumerate(patternVal):
                    tmp = 0
                    for c, lblc in enumerate(valCla):
                        for r, lblr in enumerate(lblRef):
                            if val == (lblr + lblc):
                                tmp = tmp + ttheme[r][c]
                    wntheme[i][col] = tmp

            #Theme similarity matrix
            step_theme = deepcopy(wntheme)
            for i in list(range(rdim)):
                for j in list(range(rdim)):
                    step_theme[i][j] = wntheme[i][j] / vrtWeights[i]

            self.dlg.progressBar.setValue(25)


            """Calculation of Position similarity"""

            #Calculation of centroids distance matrix
            distCent = deepcopy(mint)
            for i in refObjLyr.getFeatures():
                for j in claObjLyr.getFeatures():
                    if mint[i.id()][j.id()] == True:
                        ptoRef = i.geometry().centroid().asPoint()
                        ptoCla = j.geometry().centroid().asPoint()
                        dist = QgsGeometry().fromPointXY(ptoRef). \
                                distance(QgsGeometry().fromPointXY(ptoCla))
                        distCent[i.id()][j.id()] = dist
                    else:
                        distCent[i.id()][j.id()] = 0

            #Calculation of equivalent circle diameter reference matrix
            deqref = deepcopy(mint)
            for i in refObjLyr.getFeatures():
                for j in claObjLyr.getFeatures():
                    if mint[i.id()][j.id()] == True:
                        deqref[i.id()][j.id()] = 2 \
                            * sqrt((amint[i.id()][j.id()] + aref[i.id()]) / pi)
                    else:
                        deqref[i.id()][j.id()] = 0

            #Calculation of position matrix
            position = deepcopy(deqref)
            for i in refObjLyr.getFeatures():
                for j in claObjLyr.getFeatures():
                    if mint[i.id()][j.id()] == True:
                        position[i.id()][j.id()] = 1 - \
                            distCent[i.id()][j.id()] / deqref[i.id()][j.id()]
                    else:
                        position[i.id()][j.id()] = 0

            #Horizontal aggregation
            wposition = [list(range(rdim)) for i in list(range(cdim))]
            for r in list(range(cdim)):
                for c, v in enumerate(valCla):
                    tmp = 0
                    for j, l in enumerate(lblCla):
                        if v == l:
                            tmp = tmp + position[r][j] * amint[r][j] / aref[r]
                    wposition[r][c] = tmp

            #Vertical aggregation
            tposition = deepcopy(wtheme)
            for i in list(range(cdim)):
                for j in list(range(rdim)):
                    tposition[i][j] = wposition[i][j] * weight[i]

            wnposition = [list(range(rdim)) for i in list(range(rdim))]
            for col, lblC in enumerate(valCla):
                pattern = []
                for row, lblR in enumerate(lblRef):
                    pattern.append(lblR + lblC)
                patternVal = list(set(pattern))
                patternVal.sort()
                for i,val in enumerate(patternVal):
                    tmp = 0
                    for c, lblc in enumerate(valCla):
                        for r, lblr in enumerate(lblRef):
                            if val == (lblr + lblc):
                                tmp = tmp + tposition[r][c]
                    wnposition[i][col] = tmp

            #Position similarity matrix
            step_position = deepcopy(wnposition)
            for i in list(range(rdim)):
                for j in list(range(rdim)):
                    step_position[i][j] = wnposition[i][j] / vrtWeights[i]

            self.dlg.progressBar.setValue(50)


            """Calculation of Edge similarity"""
            #Calculaton of edge tolerance
            lmtRef = [QgsGeometry.fromPolylineXY(r.geometry().asMultiPolygon()[0][0]) \
                    for r in refObjLyr.getFeatures()]
            bffRef = [r.buffer(0.1,0) for r in lmtRef]
            lmtCla = [QgsGeometry.fromPolylineXY(c.geometry().asMultiPolygon()[0][0]) \
                    for c in claObjLyr.getFeatures()]
            bffCla = [c.buffer(epsilon,0) for c in lmtCla]

            #Horizontal aggregation
            tedge = deepcopy(mint)
            for i, r in enumerate(bffRef):
                for j, c in enumerate(bffCla):
                    if mint[i][j] == True:
                        geom = r.intersection(c)
                        tedge[i][j] = geom.length()
                    else:
                        tedge[i][j] = 0

            #Retrieving boundary of reference objects
            boundRef = [r.geometry().length() for r in refObjLyr.getFeatures()]

            #Objects' edge matrix
            edge = deepcopy(tedge)
            for i in refObjLyr.getFeatures():
                for j in claObjLyr.getFeatures():
                    if mint[i.id()][j.id()] == True:
                        tmp = tedge[i.id()][j.id()] / boundRef[i.id()]
                        if tmp > 1:
                            edge[i.id()][j.id()]= 1 / tmp
                        else:
                            edge[i.id()][j.id()] = tmp
                    else:
                        edge[i.id()][j.id()] = 0

            #Horizontal aggregation
            wedge = [list(range(rdim)) for i in list(range(cdim))]
            for r in list(range(cdim)):
                for c, v in enumerate(valCla):
                    tmp = 0
                    for j, l in enumerate(lblCla):
                        if v == l:
                            tmp = tmp + edge[r][j] * amint[r][j] / aref[r]
                    wedge[r][c] = tmp

            # Vertical aggregation
            tedge= deepcopy(wtheme)
            for i in list(range(cdim)):
                for j in list(range(rdim)):
                    tedge[i][j] = wedge[i][j] * weight[i]

            wnedge = [list(range(rdim)) for i in list(range(rdim))]
            for col, lblC in enumerate(valCla):
                pattern = []
                for row, lblR in enumerate(lblRef):
                    pattern.append(lblR + lblC)
                patternVal = list(set(pattern))
                patternVal.sort()
                for i,val in enumerate(patternVal):
                    tmp = 0
                    for c, lblc in enumerate(valCla):
                        for r, lblr in enumerate(lblRef):
                            if val == (lblr + lblc):
                                tmp = tmp + tedge[r][c]
                    wnedge[i][col] = tmp

            #Edge similarity matrix
            step_edge = deepcopy(wnedge)
            for i in list(range(rdim)):
                for j in list(range(rdim)):
                    step_edge[i][j] = wnedge[i][j] / vrtWeights[i]

            self.dlg.progressBar.setValue(75)

            """Calculation of shape similarity"""

            #Retrieving boundary of classified objects
            boundCla = deepcopy(mint)
            for i in refObjLyr.getFeatures():
                for j in claObjLyr.getFeatures():
                    if mint[i.id()][j.id()] == True:
                        boundCla[i.id()][j.id()] = j.geometry().length()
                    else:
                        boundCla[i.id()][j.id()] = 0

            #Calculation of the equal area circle (eac)
            eacRef = [sqrt(a / pi) for a in aref]
            eacCla = deepcopy(mint)
            for i in refObjLyr.getFeatures():
                for j in claObjLyr.getFeatures():
                    if mint[i.id()][j.id()] == True:
                        eacCla[i.id()][j.id()] = sqrt(j.geometry().area() / pi)
                    else:
                        eacCla[i.id()][j.id()] = 0

            #Calculation of the normlized perimeter index (npi)
            npiRef = [eacRef[i]/boundRef[i] for i, a in enumerate(eacRef)]

            npiCla = deepcopy(mint)
            for i in refObjLyr.getFeatures():
                for j in claObjLyr.getFeatures():
                    if mint[i.id()][j.id()] == True:
                        npiCla[i.id()][j.id()] = eacCla[i.id()][j.id()] \
                                                / boundCla[i.id()][j.id()]
                    else:
                        npiCla[i.id()][j.id()] = 0

            #Objects' shape matrix
            shape = deepcopy(mint)
            for i in refObjLyr.getFeatures():
                for j in claObjLyr.getFeatures():
                    if mint[i.id()][j.id()] == True:
                        tmp = npiCla[i.id()][j.id()]/npiRef[i.id()]
                        if tmp > 1:
                            shape[i.id()][j.id()]= 1 / tmp
                        else:
                            shape[i.id()][j.id()] = tmp
                    else:
                        shape[i.id()][j.id()] = 0

            #Horizontal aggregation
            wshape = [list(range(rdim)) for i in list(range(cdim))]
            for r in list(range(cdim)):
                for c, v in enumerate(valCla):
                    tmp = 0
                    for j, l in enumerate(lblCla):
                        if v == l:
                            tmp = tmp + shape[r][j] * amint[r][j]/aref[r]
                    wshape[r][c] = tmp

            #Vertical aggregation
            tshape = deepcopy(wtheme)
            for i in list(range(cdim)):
                for j in list(range(rdim)):
                    tshape[i][j] = wshape[i][j] * weight[i]

            wnshape = [list(range(rdim)) for i in list(range(rdim))]
            for col, lblC in enumerate(valCla):
                pattern = []
                for row, lblR in enumerate(lblRef):
                    pattern.append(lblR + lblC)
                patternVal = list(set(pattern))
                patternVal.sort()
                for i,val in enumerate(patternVal):
                    tmp = 0
                    for c, lblc in enumerate(valCla):
                        for r, lblr in enumerate(lblRef):
                            if val == (lblr + lblc):
                                tmp = tmp + tshape[r][c]
                    wnshape[i][col] = tmp

            #Shape similarity matrix
            step_shape = deepcopy(wnshape)
            for i in list(range(rdim)):
                for j in list(range(rdim)):
                    step_shape[i][j] = wnshape[i][j] / vrtWeights[i]

            self.dlg.progressBar.setValue(100)

            #show an save similarity metrics
            outputPath = Path(self.dlg.txtDirName.text())
            
            fileSTEPname = outputPath / "STEP_Similarity_Metrics.csv"
            outputFileSTEP = open(fileSTEPname, 'w')
            #lblSTEP = ("Category;Shape;Theme;Edge;Position\n")
            outputFileSTEP.write("Category;Shape;Theme;Edge;Position\n")            
            self.dlg.txtResults.appendPlainText("Category;Shape;Theme;Edge;Position")
            
            for i in list(range(rdim)):                
                for j in list(range(rdim)):
                    if i == j:
                        step = '%s; %s; %s; %s; %s' % \
                                (valRef[i], round(step_shape[i][j],4),
                                round(step_theme[i][j],4),
                                round(step_edge[i][j],4),
                                round(step_position[i][j],4))
                        self.dlg.txtResults.appendPlainText(step)
                        outputFileSTEP.write(step)
                        outputFileSTEP.write("\n")
            outputFileSTEP.close()

            #Save similarity matrix to files
            fileSName = outputPath / "Shape_Similarity_Matrix.csv"
            fileTName = outputPath / "Theme_Similarity_Matrix.csv"
            fileEName = outputPath / "Edge_Similarity_Matrix.csv"
            filePName = outputPath / "Position_Similarity_Matrix.csv"
            outputFileS = open(fileSName, 'w')
            outputFileT = open(fileTName, 'w')
            outputFileE = open(fileEName, 'w')
            outputFileP = open(filePName, 'w')

            outputFileS.write("Shape")
            outputFileS.write(";")
            outputFileT.write("Theme")
            outputFileT.write(";")
            outputFileE.write("Edge")
            outputFileE.write(";")
            outputFileP.write("Position")
            outputFileP.write(";")

            for i in list(range(rdim)):
                outputFileS.write(valRef[i])
                outputFileS.write(";")
                outputFileT.write(valRef[i])
                outputFileT.write(";")
                outputFileE.write(valRef[i])
                outputFileE.write(";")
                outputFileP.write(valRef[i])
                outputFileP.write(";")

            outputFileS.write("\n")
            outputFileT.write("\n")
            outputFileE.write("\n")
            outputFileP.write("\n")

            for i in list(range(rdim)):
                outputFileS.write(valRef[i])
                outputFileT.write(valRef[i])
                outputFileE.write(valRef[i])
                outputFileP.write(valRef[i])
                outputFileS.write(";")
                outputFileT.write(";")
                outputFileE.write(";")
                outputFileP.write(";")
                for j in list(range((rdim))):
                    outputFileS.write(str(round(step_shape[i][j],4)))
                    outputFileT.write(str(round(step_theme[i][j],4)))
                    outputFileE.write(str(round(step_edge[i][j],4)))
                    outputFileP.write(str(round(step_position[i][j],4)))
                    outputFileS.write(";")
                    outputFileT.write(";")
                    outputFileE.write(";")
                    outputFileP.write(";")
                outputFileS.write("\n")
                outputFileT.write("\n")
                outputFileE.write("\n")
                outputFileP.write("\n")

            outputFileS.close()
            outputFileT.close()
            outputFileE.close()
            outputFileP.close()        
            
            