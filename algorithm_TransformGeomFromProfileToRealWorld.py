# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TlugProcessing
                                 TransformGeomFromProfileToRealWorld
 TLUG Algorithms
                              -------------------
        begin                : 2018-08-27
        copyright            : (C) 2017 by Thüringer Landesanstalt für Umwelt und Geologie (TLUG)
        email                : Michael.Kuerbs@tlug.thueringen.de
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
__date__ = '2018-10-12'
__copyright__ = '(C) 2018 by Michael Kürbs by Thüringer Landesanstalt für Umwelt und Geologie (TLUG)'

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
#from .tlug_utils.LayerSwitcher import LayerSwitcher

class TransformGeomFromProfileToRealWorld(QgsProcessingAlgorithm):
    """
    Retransform point, line or polygon geometrys from profile coordinates back to real world geometry with Z values considering a baseline.
    Select a line feature or use an one feature layer as Baseline.
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
            raise QgsProcessingException(offsetExpr.parserErrorString())
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

        #tm=TerrainModel(rasterLayer, feedback)
        #lp=LaengsProfil(baseLine, tm, crsProject, feedback) # use baseLine in Projekt.crs
        #lp.calc3DProfile()
        
        linRef = LinearReferencingMaschine(baseLine, crsProject, feedback)
        
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                context, vectorLayer.fields(), vectorLayer.wkbType(), crsProject)

        try:
            total = 100.0 / vectorLayer.featureCount()
        except:
            msg = self.tr("Keine Basislinie")
            feedback.reportError(msg)
            raise QgsProcessingException(msg)
        
        
        
        i=0
        for feat in vectorLayer.getFeatures():

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

            #if not offsetFieldIndex == -1:
            #    abstand=feat.attribute(offsetFieldIndex)
            #feedback.pushInfo("GeometryType: " + str( vectorLayer.geometryType() ) + " name: " + vectorLayer.name() + " Feat: " + str( feat.geometry().wkbType() ) )
            if vectorLayer.geometryType() == 2: #Polygon
                # fill Vertices with Baseline-Breakpoints
                feat.setGeometry( self.fillPolygonVertices( feat.geometry() , linRef, crsProject, feedback) )
            #Create Real World geometry with LinearReferencingMaschine
            realWorldFeat=linRef.transformProfileFeatureToRealWorld(feat, vectorLayer.crs(), feedback, abstand, ueberhoehung)


            #Erzeuge Feature
#            realWorldFeat.setGeometry(realWorldFeat.geometry())
#            realWorldFeat.setAttributes(feat.attributes())
            #feedback.pushInfo(str(i) + ": " + realWorldFeat.geometry().asWkt())

            # Add a feature in the sink
            sink.addFeature(realWorldFeat, QgsFeatureSink.FastInsert)
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
        return 'Reverse To Real World'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

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


    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return TransformGeomFromProfileToRealWorld()

        
    #Diese Funktion füllt ein ProfilPolygon mit den Stützpunkten der Basislinie auf
    #Es entsteht ein Multipolygon
    def fillPolygonVertices(self, polygon, linRef, crs, feedback):

        listPointStation=[] #[pt, station, isBreakLine(Boolean) ]
    
        #Vertices in profil coordinates
        verticalLines = []
        for vertex in linRef.profilLine.vertices():
            station, abstand = linRef.transformToLineCoords( vertex )

            p1 = QgsPoint( station, 100000 )
            p2 = QgsPoint( station, -100000 )
            verticalLines.append( QgsGeometry().fromPolyline( [p1, p2]) )       #erstelle vertikale Linien an jedem Punkt der Basislinie
            

        #Polygon as Polyline
        lineGeom = QgsGeometry().fromPolylineXY( polygon.asPolygon()[0] )
        #get Intersections Polygon with vertikal lines
        #create LinearReferencingMaschine for Polygon-Ring in Profil coordinates
        linRefPolygon = LinearReferencingMaschine(lineGeom , crs, feedback )
        curStation = 0
        lastPoint=None
        hasIntersection=False
        #look for each line segment of the Ring if intersect a vertical line
        for segment in linRefPolygon.lineSegments:
            p1 = segment.vertexAt(0)
            listPointStation.append( [ p1, curStation, p1.x(),  False ] )

            for vLine in verticalLines:
                #feedback.pushInfo(str(curStation)+" Line: " + vLine.asWkt() + " Segment: " + segment.asWkt())
                pt, stationOnSegment = linRefPolygon.getIntersectionPointofSegment( vLine, segment )
                if not pt is None and not stationOnSegment is None:
                    station = curStation + stationOnSegment
                    p = QgsPoint( pt.asPoint()[0], pt.asPoint()[1] )
                    listPointStation.append( [ p, station, p.x(), True] )
                    hasIntersection=True
              
            
            lastPoint=segment.vertexAt(1)
            curStation = curStation + segment.length()
        
        if not hasIntersection:
            feedback.pushInfo( polygon.asWkt() )
            return polygon #No Polygon manipulation needed
        
        #add last Point of Polygon
        listPointStation.append( [lastPoint, curStation, lastPoint.x(), False] )
        # sortiere nach x (Station)
        listPointStation.sort( key=lambda x: x[2]) 

        
        polygonItems = []
        itemsPolygon =[]
        iBreakPoint = 0
        lastCurBreakItems=[]
        curBreakItems=[]
        hasBreakpoints=False
        #curBreakItems müssen noch zu nächsten hinzugefügt werden
        for elem in listPointStation:
            itemsPolygon.append( elem )
            isBreakPoint = elem[3]


            if isBreakPoint:
                curBreakItems.append(elem)
                iBreakPoint=iBreakPoint + 1
                hasBreakpoints=True
                if iBreakPoint == 2:
                    polygonItems.append( itemsPolygon )
                    itemsPolygon = []
                    iBreakPoint = 0
                    
                    #add Breakpoints
                    for breakItem in lastCurBreakItems: #always 2
                        itemsPolygon.append( breakItem ) 
                    # clear Breakpoints
                    lastCurBreakItems = curBreakItems # merke die 2 Breakpoints für das nächste Polygon
                    curBreakItems = []

    
        #add Breakpoints to last polygon of the Multipolygon
        if len( itemsPolygon ) > 0:
            polygonItems.append( itemsPolygon )
            if hasBreakpoints==True:
                #add Breakpoints
                for breakItem in lastCurBreakItems: #always 2
                    itemsPolygon.append( breakItem ) # merke die 2 Breakpoints für das nächste Polygon

        multiGeom = QgsGeometry()
        polygons=[]

        for i, pItem in enumerate(polygonItems):
            polygonPoints = []
            #sortiert die Punkte an Hand der Station (Index 1)
            pItem.sort( key=lambda x: x[1])
            feedback.pushInfo(str(i) + " pitem:" + str( pItem ))
            
            for item in pItem:
                pt=item[0]
                #feedback.pushInfo("pt: " +  str( type( pt ) ) )
                polygonPoints.append( QgsPointXY( pt.x(), pt.y() ) )
            #polygonGeom=QgsGeometry().fromPolygonXY( [ polygonPoints ] )
            polygons.append( polygonPoints )
            # if i==0:
                # multiGeom = polygonGeom
            # else:
                # multiGeom.addPart( [ polygonPoints ] )
        if len( polygons ) > 1:
        
            multiGeom = QgsGeometry().fromMultiPolygonXY( [ polygons for polyg in polygons ] )
            #feedback.pushInfo( multiGeom.asWkt() )
            return multiGeom
        else: #single Polygon
            singleGeom = QgsGeometry().fromPolygonXY( polygons )
            #feedback.pushInfo( singleGeom.asWkt() )

            return singleGeom

        
    def interpolateValue( self, a, b, xc): # a and b are lists [xa, ya] and [xb, yb]
        dx=b[0] - a[0] #xb - xa
        dy=b[1] - a[1] #yb - ya
        dxc = xc - a[0]  #xc - xa
        dyc = dxc * dy / dx 
        yc = a[1] + dyc #ya + dyc
        
        return yc
        