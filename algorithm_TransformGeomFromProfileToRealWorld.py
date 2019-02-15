# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ThToolBox
                                 TransformGeomFromProfileToRealWorld
 TLUBN Algorithms
                              -------------------
        begin                : 2018-08-27
        copyright            : (C) 2017 by Thüringer Landesamt für Umwelt, Bergbau und Naturschutz (TLUBN)
        email                : Michael.Kuerbs@tlubn.thueringen.de
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

__author__ = 'Michael Kürbs'
__date__ = '2019-02-15'
__copyright__ = '(C) 2019 by Michael Kürbs by Thüringer Landesamt für Umwelt, Bergbau und Naturschutz (TLUBN)'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterField,
                       QgsProcessingParameterExpression,
                       QgsExpression,
                       QgsExpressionContext,
                       QgsProject,
                       QgsFeature,
                       QgsFeatureRequest,
                       QgsField,
                       QgsPoint,
                       QgsPointXY,
                       QgsGeometry,
                       QgsCoordinateTransform,
                       QgsProcessingException,
                       QgsWkbTypes)
from .tlug_utils.LinearReferencingMaschine import LinearReferencingMaschine
from .tlug_utils.TerrainModel import TerrainModel
from .tlug_utils.LaengsProfil import LaengsProfil
from .tlug_utils.LayerUtils import LayerUtils
from PyQt5.QtGui import QIcon
import os
import math

class TransformGeomFromProfileToRealWorld(QgsProcessingAlgorithm):
    """
    Retransform point, line or polygon geometrys from profile coordinates back to real world geometry with Z values considering a baseline.
    A baseline can have breakpoints.
    Select one line feature or use an one feature layer as Baseline.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    INPUTVECTORLAYER = 'INPUTVECTORLAYER'
    INPUTBASELINE = 'INPUTVECTOR'
    INPUTZFACTOR = 'INPUTZFACTOR'
    OFFSETFIELD = 'OFFSETFIELD'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUTVECTORLAYER,
                self.tr('Layer in Profile Coordinates'),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUTBASELINE,
                self.tr('Profil Baseline'),
                [QgsProcessing.TypeVectorLine]
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.INPUTZFACTOR,
                self.tr('Z-Factor / Ueberhoehung'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=10,
                optional=False,
                minValue=0,
                maxValue=100
                
            )
        )
        self.addParameter(
            QgsProcessingParameterExpression(
                self.OFFSETFIELD,
                self.tr('Offset'),
                "0",
                self.INPUTVECTORLAYER,#DoTo: set Datatyp Numeric
                optional=True

            )
        )


        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Real World Geometries')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        ueberhoehung = self.parameterAsInt(parameters, self.INPUTZFACTOR, context)
        vectorLayer = self.parameterAsVectorLayer(parameters, self.INPUTVECTORLAYER, context)
        baseLineLayer = self.parameterAsVectorLayer(parameters, self.INPUTBASELINE, context)
        offsetFieldName = self.parameterAsString(parameters, self.OFFSETFIELD, context)
        #offsetFieldIndex=-1
        
        #if not offsetFieldName=="":
            #fields = vectorLayer.fields()
            #offsetFieldIndex = vectorLayer.fields().lookupField(offsetFieldName)
        offsetExpr=QgsExpression(offsetFieldName)
        if offsetExpr.hasParserError():
            feedback.reportError("Offset Expression failed: " + offsetExpr.parserErrorString())
            offsetExpr="0"
            
        offsetExprContext = QgsExpressionContext()
        baseLineFeature=None
        baseLine=None
        #Basline Layer must have only 1 Feature
        if baseLineLayer.featureCount()==1:
        #baseLine must be the first feature
            baseLineFeature=next(baseLineLayer.getFeatures(QgsFeatureRequest().setLimit(1)))
            baseLine=baseLineFeature.geometry()
        elif len(baseLineLayer.selectedFeatures())==1:
            selection=baseLineLayer.selectedFeatures()
            #baseLine must be the first feature
            selFeats=[f for f in selection]
            baseLineFeature=selFeats[0]
            baseLine=baseLineFeature.geometry() 
        else:
            msg = self.tr("Error: BaseLine layer needs exactly one line feature! "+ str(baseLineLayer.featureCount()) + " Just select one feature!")
            feedback.reportError(msg)
            raise QgsProcessingException(msg)

        #check if vectorlayer has Features
        if vectorLayer.featureCount()==0:
            msg = self.tr("Error: Layer " , vectorLayer.name() , "is emty! ")
            feedback.reportError(msg)
            raise QgsProcessingException(msg)



        #take CRS from Project
        crsProject=QgsProject.instance().crs()         
        #check if layers have the same crs
        if not baseLineLayer.crs().authid()==crsProject.authid():
            # if not, transform to raster crs()
            trafo=QgsCoordinateTransform(baseLineLayer.crs(),crsProject,QgsProject.instance())
            #transform BaseLine
            opResult=baseLine.transform(trafo,QgsCoordinateTransform.ForwardTransform, False)

        
        linRef = LinearReferencingMaschine(baseLine, crsProject, feedback)
        
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                context, vectorLayer.fields(), vectorLayer.wkbType(), crsProject)

        try:
            total = 100.0 / vectorLayer.featureCount()
        except:
            msg = self.tr("Keine Basislinie")
            feedback.reportError(msg)
            raise QgsProcessingException(msg)
        
        #check Selection of Inputlayer
        #if yes, use just the selection
        processfeatures=None
        if len(vectorLayer.selectedFeatures()) == 0:
            processfeatures = vectorLayer.getFeatures()
        else:
            processfeatures = vectorLayer.selectedFeatures() 

        
        i=0
        for feat in processfeatures: #vectorLayer.getFeatures():

            abstand=0
            offsetExprContext.setFeature( feat )
            try:
                abstand = offsetExpr.evaluate( offsetExprContext )
            except:
                msg = self.tr("Error while calculating Offset from Expression. Feature " + str(feat.attributes()) )
                feedback.reportError(msg)
                raise QgsProcessingException(msg)
            try:
                #check for numeric Expression Data type 
                a=int(abstand)
                b=float(abstand) 
            except:
                msg = self.tr("Error Offset Experession result must be numeric, not " + str( type( abstand )) )
                feedback.reportError(msg)
                raise QgsProcessingException(msg)
                
            subFeatureList=[]

            layerUtils=LayerUtils( crsProject, feedback)
            subFeatureList=layerUtils.multiPartToSinglePartFeature( feat )

            #preparation of profile geometrys
            prepSubFeatureList=[]
            for iP, f in enumerate(subFeatureList):
                if linRef.isSimpleLine or vectorLayer.geometryType() == 0 or vectorLayer.geometryType() == 1: #Point (Line nur temporär):
                    prepSubFeatureList.append( f ) #keep old feature                
                else:
                    # Basisline hat Knickpunkte, Profilgeometrien müssen ggf. mit zusätzlichen Stützpunkten gefüllt werden
                    # Baseline has breakpoints, we have to fill the profile geometrys with additional vertices
                    filledSingleGeom = None
                    if vectorLayer.geometryType() == 2: #Polygon
                        filledSingleGeomList = self.fillPolygonVertices( f.geometry() , linRef, crsProject, feedback)
                    #elif vectorLayer.geometryType() == 1: #Line
                    
                    if len(filledSingleGeomList) > 0:
                        for g in filledSingleGeomList:
                            #create a feature for each filled sub geometry
                            filledFeature=QgsFeature( f )
                            filledFeature.setGeometry( g )
                            filledFeature.setAttributes( f.attributes() )
                            prepSubFeatureList.append( filledFeature )
                    else:
                        prepSubFeatureList.append( f ) #keep old feature
                        feedback.reportError( "Feature geometry can not be filled: " + str( f.attributes() ) )


                
            #Back to Real World Transformation for each sub Feature
            realWorldSubFeatureList=[]
            for pFeat in prepSubFeatureList:
            
                #Create Real World geometry with LinearReferencingMaschine
                realWorldFeat=linRef.transformProfileFeatureToRealWorld( pFeat, vectorLayer.crs(), feedback, abstand, ueberhoehung )
                realWorldSubFeatureList.append( realWorldFeat )
                
            ##### ggf features könnten hier wieder gruppiert werden ######
                
            #write real worl Features to output layer
            for rwFeat in realWorldSubFeatureList:
                sink.addFeature(rwFeat, QgsFeatureSink.FastInsert)
 
 
            i=i+1
            # Update the progress bar
            feedback.setProgress(int(i * total))

        msgInfo=self.tr(str(i) + " Features were transformed to real world coordinates")
        feedback.pushInfo(msgInfo)
        # Return the results of the algorithm. In this case our only result is
        return {self.OUTPUT: dest_id}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return self.tr('Reverse_To_Real_World')

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Reverse To Real World')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'To Profile Coordinates'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr(self.__doc__)

   
    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__),'icons/TransformGeomFromProfileToRealWorld_Logo.png'))


    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return TransformGeomFromProfileToRealWorld()

    #This function add's new vertices to a polygon geometry in preparation vor retransform a profile object(polygon) back to a real-world feature, if the profile baseline has vertices 
    #Diese Funktion füllt ein ProfilPolygon mit den Stützpunkten der Basislinie auf
    #Wenn die Profil-Basislinie Knickpunkte hat, müssen die zu überführendes Objekt geprüft werden, ob sie entlang eines solchen Knickes verlaufen.
    #Falls ja, muss in der Profilgeometrie des Objektes der Knick als Vertikale Unterbrechung mit eingefügt werden
    #Es entsteht ein Array mit Single Polygonen [Polygon]
    def fillPolygonVertices(self, polygon, linRef, crs, feedback):
    
        #Vertices in profil coordinates
        
        #Check if the profile baseline has breakpointserstelle. If yes, create vertikal break lines for intersection with profile objects
        #Falls die Profil-Basislinie Knickpunkte hat erstelle vertikale Linien zur Verscheideung mit den Profilobjekten
        verticalLines = []
        for vertex in linRef.profilLine.vertices():
            station, abstand = linRef.transformToLineCoords( vertex )

            p1 = QgsPoint( station, 100000 )
            p2 = QgsPoint( station, -100000 )
            verticalLines.append( QgsGeometry().fromPolyline( [p1, p2]) )       

        #bereite polygone vor, für Schnittpunkt-Ermittlung
        #preparate polygons for Intersection point determination
        polygons=[]
        lineGeom = None
        if polygon.isMultipart():
            #darf nicht sein!!
            msg = self.tr("Multipolygon konnte nicht aufgeteilt werden!")
            feedback.reportError(msg)
            raise QgsProcessingException(msg)

        else:

            #Polygon as Polyline
            lineGeom = QgsGeometry().fromPolylineXY( polygon.asPolygon()[0] )#( polygon.asPolygon()[0] )
            #feedback.pushInfo("PreFillPolygon " + str( lineGeom.asWkt() ))
        #get Intersection point from Polygon with vertikal lines
        #create LinearReferencingMaschine for Polygon-Ring in Profil coordinates
        #Für den Umring des Polygons müssen die Schnittpunkte mit den vertikalen Unterbrechnungslinien ermittelt werden
        #Dazu wird für den Umring die Lineare Referenzierung genutzt, welche bereits eine Funktion hat, die den Schnittpunkt mit einer Linie ermittelt  
        
        linRefPolygon = LinearReferencingMaschine(lineGeom , crs, feedback )
        curStation = 0
        lastPoint=None
        hasIntersection=False
        #Liste der Punkte des Polygons, inklusive der zusätzlich Stützpunkte an den Schnittpunkten mit den vertikalen Unterbrechungen
        #List the polygons points included the additional vertices at the vertical lines intersections 
        listPointStation=[] #[pt, station, isBreakLine(Boolean) ]
        
        #add the vertices of this polygon
        for segment in linRefPolygon.lineSegments:
            pi = segment.vertexAt(0)
            lastPoint=segment.vertexAt(1)
            #First vertex to list 
            listPointStation.append( [ pi, curStation, pi.x(),  False ] )
            curStation = curStation + segment.length()
        listPointStation.append( [ lastPoint, curStation, lastPoint.x(),  False ] )

        #look, if there are breaks related of the vertical line intersection
        #prüfe, ob es Unterbrechungen durch die vertikalen Unterbrechnungslinien gibt und füge sie zur Stützpunktliste hinzu           
        breaks=[] # List of [ [break, break, ..], [break, break, break, ..],[break, break, ..]   ]
        breakPoints=[]
        for vLine in verticalLines:
            #feedback.pushInfo(str(curStation)+" Line: " + vLine.asWkt() + " Segment: " + segment.asWkt())
            #Schnittpunkt
            try:
                pts, stationOnSegments = linRefPolygon.getIntersectionPointsofPolyLine( vLine ) #getIntersectionPointofSegment( vLine, segment )
                if not pts is None and not stationOnSegments is None:
                    #es können mehrere Schnittpunkte sein
                    #feedback.pushInfo("Schnittpunkte: " + str( len(pts) ) )
                    
                    for i, pnt in enumerate(pts):
                        stationOnRing = stationOnSegments[i] #Station auf Polygonumring
                        p = QgsPoint( pnt.asPoint()[0], pnt.asPoint()[1] )
                        #Schnittpunkt kommt mit in Punktliste des Teil-Polygons
                        listPointStation.append( [ p, stationOnRing, p.x(), True] )
                        breakPoints.append( [ p, stationOnRing, p.x(), True] )
                        #feedback.pushInfo("_ " + str( p.asWkt() ))
                        hasIntersection=True
                    #breaks.append( lineBreakPoints )
            except Exception as err:
                msg = self.tr("Fehler beim Holen der Schnittpunkte mit den Vertikalen Unterbrechungen!")
                feedback.reportError(msg  +" "+ str(err.args) + ";" + str(repr(err)))
                raise QgsProcessingException(msg)

        #Falls keine Überschneidung mit einer Unterbrechungslinie, ausgangspolygon beibehalten werden
        #If no intersection with vertical lines, keep source polygon
        if not hasIntersection:
            #feedback.pushInfo( polygon.asWkt() )
            return [polygon] #No Polygon manipulation needed
            
        try:
            if len(listPointStation)==0:
                msg = self.tr("Fehler Liste listPointStation ist leer.")
                raise QgsProcessingException(msg)
                #return []
        except Exception as err:
            msg = self.tr("Fehler Liste listPointStation ist None.")
            #feedback.reportError(msg  +" "+ str(err.args) + ";" + str(repr(err)))
            raise QgsProcessingException(msg)

        
        # sortiere nach x (Station)
        # sort by x (station-based)
        listPointStation.sort( key=lambda x: x[2]) 
        breakPoints.sort( key=lambda x: x[2]) 
        
        try:
            polygonItems = self.splitListPointStationByXBreaks(listPointStation, breakPoints, feedback)
            feedback.pushInfo("Polygone was separated by baseLine vertices to " + str( len( polygonItems ) ) + " parts.")

        except Exception as err:
            msg = self.tr("Fehler bei Methode splitListPointStationByXBreaks()")
            feedback.reportError(msg  +" "+ str(err.args) + ";" + str(repr(err)))
            raise QgsProcessingException(msg)


        #Sortinerung nach Station auf Plygonumring, liefert die richtige Reihenfolge der Polygonstützpunkte
        polygons=[]
        for i, pItem in enumerate(polygonItems):
            polygonPoints = []
            #sortiert die Punkte an Hand der Station auf dem Polygonumring(Index 1) um die richtige Punktreihenfolge zu erhalten
            #order by station on the polygon circle to get the right point sequence for each sub polygon
            pItem.sort( key=lambda x: x[1])
            #feedback.pushInfo(str(i) + " pitem:" + str( pItem ))
            #feedback.pushInfo( "Wkt" + "\t" +  "part"+ "\t" +  "order" + "\t"+  "statOnRing" + "\t" + "xS" + "\t" + "isBrkPoint" )
            
            for j, item in enumerate(pItem):
                pt=item[0]
                isBrkPoint=item[3]
                statOnRing=item[1]
                xS=item[2]
                #feedback.pushInfo( pt.asWkt() + "\t" +  str( i )+ "\t" +  str( j )+ "\t" +  str( statOnRing ) + "\t" + str(xS) + "\t" + str(isBrkPoint) )
                polygonPoints.append( QgsPointXY( pt.x(), pt.y() ) )
            polygons.append( polygonPoints )
            # if i==0:
                # multiGeom = polygonGeom
            # else:
                # multiGeom.addPart( [ polygonPoints ] )

        # neu gebildete Teilpolygone werden einzeln in Liste übergeben
        # new createt sub polygons will be returned separately in a list [ QgsGeometry ]
        polygonOutputList=[]
        if len( polygons ) > 1:
            #feedback.pushInfo("Sub Polygons: ")

            for polyg in polygons:
                pGeom=QgsGeometry().fromPolygonXY( [ polyg ] )
                polygonOutputList.append( pGeom )
                #feedback.pushInfo("End Filled Sub: " + str( pGeom.asWkt() ))
            multiGeom = QgsGeometry()
            multiGeom = QgsGeometry().fromMultiPolygonXY( [ polygons for polyg in polygons ] )
            #feedback.pushInfo( multiGeom.asWkt() )
            #feedback.pushInfo("End Filled Multi: " +  multiGeom.asWkt() )

            #return multiGeom
        else: #single Polygon
            singleGeom = QgsGeometry().fromPolygonXY( polygons )
            #feedback.pushInfo("End Filled Single: " +  singleGeom.asWkt() )
            polygonOutputList.append(singleGeom)

            #return singleGeom
        return polygonOutputList
        
    def getBreaksAtX(self, x, breakValsX, feedback):
        breaks=[]
        i=0
        for item in breakValsX:
            xItem=item[2]
            pt=item[0]
            isBrkPoint=item[3]
            statOnRing=item[1] 
            if xItem==x:
                breaks.append(item)
                i=i+1

        return breaks

    def splitListPointStationByXBreaks(self, listPointStation, breakValsX, feedback):
    
        itemsPolygon=[]
        
        endOfLastSplit=[]
        iLastSplit=0
        iBreak=0 
        curXBreak=-9999999 #set the first xBreak
        
        #iLastBreak=-1
        xLastBreak=-9999999
        lastBreaks=[]
        hasNext=True
        schleifen=0
        cnt=0 # Counter
        while(hasNext):
            try:
            
                if iBreak == len(breakValsX):#kein Break mehr vorhanden
                    tempList=listPointStation[iLastSplit:] #Erstellt einen Slice bis zum Ende
                    if len(tempList)>0:
                        if len(lastBreaks) > 0:# Schaue ob es vorherige Breakpoints gibt
                            for brk in lastBreaks:
                                tempList.append( brk ) # fügt die vorangegangenen Breakpoints an
                        itemsPolygon.append(tempList)#Übergebe letztes TeilPolygon
                    hasNext=False # Beende Schleife
                elif listPointStation[cnt][2] > breakValsX[iBreak][2]:#Vergleiche X-Wert, 
                    #Wenn X größer als der X-Wert der aktuellen vertikalen Unterbrechung, dann erstelle Slice
                    curXBreak=breakValsX[ iBreak ][ 2 ]
                    tempList=listPointStation[iLastSplit:cnt] #Erstellt einen Slice
                    if len( tempList ) > 0:
                        if len(lastBreaks) > 0:# Schaue ob es vorherige Breakpoints gibt
                            for brk in lastBreaks:
                                tempList.append( brk ) # fügt die vorangegangenen Breakpoints an
                        if iBreak < len(breakValsX):
                            tempList.append( breakValsX[ iBreak ] ) # fügt die abschließenden Breakpoints an
                            lastBreaks=self.getBreaksAtX( curXBreak, breakValsX, feedback ) #merke Break X-Wert für nachfolgendes TeilPolygon
                            
                        iLastSplit=cnt
                    iBreak=iBreak+1
                    
                    #keep cnt
                    if len(tempList)>0:
                        itemsPolygon.append(tempList) #Übergebe TeilPolygon
                    

                    # feedback.pushInfo( "Wkt" + "\t" +  "part"+ "\t" +  "order" + "\t"+  "statOnRing" + "\t" + "xS" + "\t" + "isBrkPoint" )
                    
                    # for j, item in enumerate(tempList):
                        # pt=item[0]
                        # isBrkPoint=item[3]
                        # statOnRing=item[1]
                        # xS=item[2]
                        # feedback.pushInfo( pt.asWkt() + "\t" +  str( cnt )+ "\t" +  str( j )+ "\t" +  str( statOnRing ) + "\t" + str(xS) + "\t" + str(isBrkPoint) )
                        

                else:
                    cnt=cnt+1
                schleifen=schleifen+1
            except Exception as err:
                msg = self.tr("Fehler beim Splitten der Stützpunktliste!")
                feedback.reportError(msg  +" "+ str(err.args) + ";" + str(repr(err)))
                raise QgsProcessingException(msg)
                
            
        return itemsPolygon
        
    #def createSlice(self, counter, iLastSplit, feedback)
    
    def interpolateValue( self, a, b, xc): # a and b are lists [xa, ya] and [xb, yb]
        dx=b[0] - a[0] #xb - xa
        dy=b[1] - a[1] #yb - ya
        dxc = xc - a[0]  #xc - xa
        dyc = dxc * dy / dx 
        yc = a[1] + dyc #ya + dyc
        
        return yc
        