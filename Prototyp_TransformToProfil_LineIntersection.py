import sys
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsVectorFileWriter
from qgis.core import QgsVectorDataProvider
from qgis.core import QgsPoint
from qgis.core import QgsFeature
from qgis.core import QgsGeometry
from qgis.core import QgsError
from qgis.core import QgsField
#from qgis.core import QgsWKBTypes
from qgis.core import QgsRaster
from qgis.core import * #QGis
from qgis.PyQt.QtCore import QObject


import datetime
import struct
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly
#from .RasterInterpolator import RasterInterpolator
    
class TerrainModel(QObject):
    
    def __init__(self, rasterLayer): 
        self.rasterLayer=rasterLayer
        self.dataProv = rasterLayer.dataProvider()

        self.myExtent = self.dataProv.extent()
        self.theWidth = self.rasterLayer.width()
        self.theHeight = self.rasterLayer.height()
        self.pixelSizeX=self.rasterLayer.rasterUnitsPerPixelX()
        self.pixelSizeY=self.rasterLayer.rasterUnitsPerPixelY()
        #mittler Rasterweite aus xSize und ySize
        self.rasterWidth=(self.pixelSizeX + self.pixelSizeY) / 2 
        
        dataset = gdal.Open(self.rasterLayer.source(), GA_ReadOnly)
        geotransform = dataset.GetGeoTransform()
        bandNo=1
        band = dataset.GetRasterBand(bandNo)
        self.nodata=band.GetNoDataValue()
        bandtype = gdal.GetDataTypeName(band.DataType)
        interpolMethod=1 #0=nearestNeighbor, 1=linear 2x2 Pixel, 2=bicubic 4x4 Pixel
        self.interpolator=RasterInterpolator(rasterLayer, interpolMethod, bandNo, dataset)
        #print("width",self.rasterLayer.dataProvider().width())
        
    def addZtoPointFeatures(self, inputPoints, fieldIdWithZVals=-1, override=True):
        #pointsListZ=[] #list of QgsFeature()
        featuresWithZ=[]

        #try:
            
        #check if pointsLayer is emty
        #if inputPoints.featureCount!=0:
        for feat in inputPoints:
            #if geom.hasZ==False or geom.hasZ==True and override==True:
            # get Raster Values for each point feature
            featZ=QgsFeature() #Copy of the Feature
            geom=feat.geometry()
            pinPoint=None
            if geom.isMultipart():
                pinPoint=geom.vertexAt(0) #nimm den ersten Punkt, wenn es ein MultiPoint ist
            else:
                pinPoint=geom.asPoint()
            rastVal=None
            if fieldIdWithZVals > -1:
                rastVal=feat[fieldIdWithZVals]
            else: #hole Z-Wert von DGM
                rastVal = self.interpolator.linear(pinPoint)            #QgsPointXY(4459566.0, 5613959.0))
            #print(geom.asWkt(), pinPoint.asWkt(),"rastVal", rastVal)
            #rastSample = rasterLayer.dataProvider().identify(pinPoint, QgsRaster.IdentifyFormatValue).results()

            ptZ=QgsPoint(pinPoint.x(), pinPoint.y(), rastVal)
            wkt="PointZ(" + str(pinPoint.x()) + " " + str(pinPoint.y()) + " " + str(rastVal) + ")"
            geomZ=QgsGeometry.fromWkt(wkt)
            #print(geom.asWkt(), "Z:", rastVal, geomZ)

            featZ.setGeometry(geomZ)
            featZ.setAttributes(feat.attributes())
            featuresWithZ.append(featZ)
            #print(featZ.geometry().asWkt())
        print("addZtoPointFeatures", len(featuresWithZ), "Objekte")
        return featuresWithZ

    def addZtoPoints(self, inputPoints, fieldIdWithZVals=-1, override=True):
        pointsListZ=[] #list of QgsPoint()
        #featuresWithZ=[]

        #try:
            
        for point in inputPoints:
            #if geom.hasZ==False or geom.hasZ==True and override==True:
            # get Raster Values for each point

            rastVal=None
            if fieldIdWithZVals > -1:
                rastVal=feat[fieldIdWithZVals]
            else: #hole Z-Wert von DGM
                rastVal = self.interpolator.linear(point)            #QgsPointXY(4459566.0, 5613959.0))
            #rastSample = rasterLayer.dataProvider().identify(pinPoint, QgsRaster.IdentifyFormatValue).results()
            #for rastVal in rastSample:
            #rastVal=rastSample[1]
            #ptZ=QgsPoint(point.x(), point.y(), rastVal)
            #wkt="PointZ(" + str(point.x()) + " " + str(point.y()) + " " + str(rastVal) + ")"
            #geomZ=QgsGeometry.fromWkt(wkt)
            #print(point.asWkt(), "Z:", rastVal, geomZ)
            #print(geomZ.asWkt())
            pointsListZ.append(QgsPoint(point.x(), point.y(), rastVal))

        #else:
        #    raise Exception(self.tr('source layer is emty'))
        
        #Look if new features are there

                
        #except Exception as e:
        #    print("Fehler addZtoPoints")#e.errno, e.strerror)

        
        return pointsListZ

from qgis.core import QgsRaster, QgsRectangle
from qgis.PyQt.QtCore import QObject

try:
    from scipy import interpolate
    from numpy import asscalar
    ScipyAvailable = True
except ImportError:
    ScipyAvailable = False


def isin(value, array2d):
    return bool([x for x in array2d if value in x])


class RasterInterpolator():
    def __init__(self, rasterLayer, interpolMethod, bandNo, gdalDataset):
        self.dataProv = rasterLayer.dataProvider()
        self.interpolMethod = interpolMethod
        self.bandNo=bandNo
        self.band = gdalDataset.GetRasterBand(bandNo)
        if self.band.GetNoDataValue():
            self.noDataValue = self.band.GetNoDataValue()
        else:
            self.noDataValue = None
        self.myExtent = self.dataProv.extent()
        self.theWidth = self.dataProv.xSize()
        self.theHeight = self.dataProv.ySize()
        
        # if interpolMethod == 0:
            # self.interpolate = lambda(thePoint): self.nearestNeighbor(thePoint)
        # elif interpolMethod == 1:
            # self.interpolate = lambda(thePoint): self.linear(thePoint)
        # elif interpolMethod == 2:
            # self.interpolate = lambda(thePoint): self.bicubic(thePoint)

    def nearestNeighbor(self, thePoint):
        ident = self.dataProv.identify(thePoint, QgsRaster.IdentifyFormatValue)
        value = None
        if ident is not None:  # and ident.has_key(choosenBand+1):
            try:
                value = float(ident.results()[self.band])
            except TypeError:
                value = None
        if value == self.noDataValue:
            return None
        return value

    def linear(self, thePoint):
        # see the implementation of raster data provider, identify method
        # https://github.com/qgis/Quantum-GIS/blob/master/src/core/raster/qgsrasterdataprovider.cpp#L268
        x = thePoint.x()
        y = thePoint.y()
        xres = self.myExtent.width() / self.theWidth
        yres = self.myExtent.height() / self.theHeight
        col = round((x - self.myExtent.xMinimum()) / xres)
        row = round((self.myExtent.yMaximum() - y) / yres)
        xMin = self.myExtent.xMinimum() + (col-1) * xres
        xMax = xMin + 2*xres
        yMax = self.myExtent.yMaximum() - (row-1) * yres
        yMin = yMax - 2*yres
        pixelExtent = QgsRectangle(xMin, yMin, xMax, yMax)
        myBlock = self.dataProv.block(self.bandNo, pixelExtent, 2, 2)
        # http://en.wikipedia.org/wiki/Bilinear_interpolation#Algorithm
        v12 = myBlock.value(0, 0)
        v22 = myBlock.value(0, 1)
        v11 = myBlock.value(1, 0)
        v21 = myBlock.value(1, 1)
        if self.noDataValue in (v12, v22, v11, v21):
            return None
        x1 = xMin+xres/2
        x2 = xMax-xres/2
        y1 = yMin+yres/2
        y2 = yMax-yres/2
        value = (v11*(x2 - x)*(y2 - y)
               + v21*(x - x1)*(y2 - y)
               + v12*(x2 - x)*(y - y1)
               + v22*(x - x1)*(y - y1)
               )/((x2 - x1)*(y2 - y1))
        if value is not None and value == self.noDataValue:
            return None
        return value

    def bicubic(self, thePoint):
        # see the implementation of raster data provider, identify method
        # https://github.com/qgis/Quantum-GIS/blob/master/src/core/raster/qgsrasterdataprovider.cpp#L268
        x = thePoint.x()
        y = thePoint.y()
        xres = self.myExtent.width() / self.theWidth
        yres = self.myExtent.height() / self.theHeight
        col = round((x - self.myExtent.xMinimum()) / xres)
        row = round((self.myExtent.yMaximum() - y) / yres)
        xMin = self.myExtent.xMinimum() + (col-2) * xres
        xMax = xMin + 4*xres
        yMax = self.myExtent.yMaximum() - (row-2) * yres
        yMin = yMax - 4*yres
        pixelExtent = QgsRectangle(xMin, yMin, xMax, yMax)
        myBlock = self.dataProv.block(self.bandNo, pixelExtent, 4, 4)
        # http://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.interp2d.html
        vx = [xMin+.5*xres, xMin+1.5*xres, xMin+2.5*xres, xMin+3.5*xres]
        vy = [yMin+.5*yres, yMin+1.5*yres, yMin+2.5*yres, yMin+3.5*yres]
        vz = [[myBlock.value(3, 0), myBlock.value(3, 1), myBlock.value(3, 2), myBlock.value(3, 3)],
              [myBlock.value(2, 0), myBlock.value(2, 1), myBlock.value(2, 2), myBlock.value(2, 3)],
              [myBlock.value(1, 0), myBlock.value(1, 1), myBlock.value(1, 2), myBlock.value(1, 3)],
              [myBlock.value(0, 0), myBlock.value(0, 1), myBlock.value(0, 2), myBlock.value(0, 3)]]
        if myBlock.hasNoDataValue()and isin(self.noDataValue, vz):
            return None
        fz = interpolate.interp2d(vx, vy, vz, kind='cubic')
        value = asscalar(fz(x, y)[0])
        if value is not None and value == self.noDataValue:
            return None
        return value

from qgis.PyQt.QtCore import QObject
from qgis.core import *
from qgis.core import QgsGeometry, QgsFeature,QgsPoint
import math
#from .LinearReferencingMachine import LinearReferencingMachine


class LaengsProfil(QObject):
    
    def __init__(self, srcProfilLine, terrainModel):
        self.srcProfilLine=srcProfilLine
        self.terrainModel=terrainModel
        #init Linear Referencing
        self.linearRef=LinearReferencingMachine(srcProfilLine)
        self.detailedProfilLine=None
        
        self.profilLine3d=None
    #Erstellt eine Polyline mit Z-Werten
    def calc3DProfile(self):

        print("linearRef.verdichtePunkte", "rasterWidth", self.terrainModel.rasterWidth)
        #insert new vertices on raster cells
        self.detailedProfilLine=self.linearRef.verdichtePunkte(self.terrainModel.rasterWidth)
        #sample values from Rasters
        points3D=self.terrainModel.addZtoPoints(self.detailedProfilLine.vertices())
        #Create Geometry
        profilLine3d=QgsGeometry.fromPolyline(points3D)
        self.profilLine3d = profilLine3d
        return profilLine3d
        
    #Diese Funktion uebersetzt eine Geometrie in eine ProfilGeometrie, an Hand von Z-Koorinaten und eine Basislinie(X-Achse)
    def extractProfilGeom(self, geom, zFactor, baseLine):
        #print("extractProfilGeom for", geom.asWkt())
        multiGeom = QgsGeometry()
        geometries = []
        wkb=geom.asWkb() 
        #Umwandeln in OGR-Geometry um auf Z.Kooridnate zuzugreifen
        #geom_ogr = ogr.CreateGeometryFromWkb(wkb)
        #print(geom.type(),geom.wkbType())#, str(ogr.GetGeometryType()))
        if "Point" in geom.asWkt(): #geom.type()==1: #Point
            if geom.isMultipart():
                multiGeom = geom.asMultiPoint()
                for i in multiGeom:
                    points=[]
                    for pxy in i:
                        #print("alt", pxy.x(), pxy.y(), pxy.z())
                        station, abstand=self.linearRef.transformToLineCoords(pxy)
                        if not station is None and not abstand is None:
                            ptProfil=QgsPoint(station, pxy.z() * zFactor)
                            #print("Profil", ptProfil.x(), ptProfil.y())
                            points.append(ptProfil)
                    geometries.append(QgsGeometry().fromPoint(points))
            else:
                pxy=geom.vertexAt(0)
                #print(geom.wkbType(),"alt",geom.asWkt())
                station, abstand=self.linearRef.transformToLineCoords(pxy)
                if not station is None and not abstand is None:
                    ptProfil=QgsPoint(station, pxy.z() * zFactor)
                    #print("Profil", ptProfil.x(), ptProfil.y())
                    geometries.append(ptProfil)
        elif "Line" in geom.asWkt(): #geom.type()==2: # Line
            if geom.isMultipart():
                multiGeom = geom.asMultiPolyline()
                for i in multiGeom:
                    points=[]
                    for elem in i:
                        pxy=elem.asPoint()
                        station, abstand=self.linearRef.transformToLineCoords(pxy)
                    
                        ptProfil=QgsPoint(station, pxy.z() * zFactor)
                        print(pxy,"-m->", ptProfil.asWkt())
                        points.append(ptProfil)
                    prLine=QgsGeometry().fromPolyline(points)
                    geometries.append(prLine)
                    print("profilGeom", prLine.asWkt())   
            else:# Single Feature
                points=[]
                for pxy in geom.vertices():
                    station, abstand=self.linearRef.transformToLineCoords(pxy)
                    ptProfil=QgsPoint(station, pxy.z() * zFactor)
                    print(pxy,"-s->", ptProfil.asWkt())
                    points.append(ptProfil)
                prLine=QgsGeometry().fromPolyline(points)
                geometries.append(prLine)
                print("profilGeom", prLine.asWkt())
    
        elif "Polygon" in geom.asWkt(): # geom.type()==3: # Polygon
            if geom.isMultipart():
                multiGeom = geom.asMultiPolygon()
                for i in multiGeom:
                    points=[]
                    for pxy in i:
                        station, abstand=self.linearRef.transformToLineCoords(pxy)
                        ptProfil=QgsPoint(station, pxy.z() * zFactor)
                        points.append(QgsPoint(pxy.x(), pxy.y()))
                    geometries.append(QgsGeometry().fromPolygon(points))
            else:# Single Feature
                points=[]
                for pxy in geom.vertices():
                    station, abstand=self.linearRef.transformToLineCoords(pxy)
                    ptProfil=QgsPoint(station, pxy.z() * zFactor)
                    points.append(QgsPoint(pxy.x(), pxy.y()))
                geometries.append(QgsGeometry().fromPolygon(points))
        else:
            print("def extractProfilGeom: Geometrietyp", geom.type(),geom.wkbType(),geom.asWkt(), "nicht zugeordnet")
        #print("Single:", len(geometries), "Geometrien")
        
        return geometries
        
from qgis.core import *
from qgis.PyQt.QtCore import QObject
import math

class LinearReferencingMachine(QObject):
    
    def __init__(self, profilLine3d): #QgsVectorLayer, QgsLinestringZ
        
        self.profilLine3d=profilLine3d
        self.lineSegments=self.extractLineSegments(profilLine3d)
        
    def extractLineSegments(self, geom):
        points=self.getVertices(geom)
        #create the lines
        lines=[]
        i=0 # Line number
        while i < len(points)-1:
            p1=points[i]
            p2=points[i+1]
            lineGeom=QgsGeometry.fromPolyline([p1,p2])
            lines.append(lineGeom)
            i=i+1
        return lines

    #liefert die Stuetzpunkte einer Single-Geometrie
    def getVertices(self, geom):
        v_iter = geom.vertices()
        points=[]

        while v_iter.hasNext():
            pt = v_iter.next()
            points.append(pt)
            #print(pt.x(), pt.y())
        return points   
        
    def getStationAbstandForPoint(self, point): #QgsPoint
        pass

    def createSpatialIndex(self, vectorLayer):
        for feat in vectorLayer.getFeatures():
            index=QgsSpatialIndex()
            index.insertFeature(feat)
        return index
        

    def calcImageWith(self, line, zellWidth):
        len=line.length()
        imageWidth=len/zellWidth #Anzahl der Pixel in der Breite
        return imageWidth
        
    def getFeaturesOnBaseLine(self, srcLayer, bufferWidth):
        #print("getFeaturesOnBaseLine", srcLayer.name())
        positionsOnLine=[]
        geomClip=self.profilLine3d.buffer(bufferWidth,1)
        #QgsFeatureRequest liefert alle Punkte, die zur Linie gehoeren
        cands = srcLayer.getFeatures(QgsFeatureRequest().setFilterRect(geomClip.boundingBox()))
        # #indexbasierte Abfrage mit Bounding Box
        # index=self.createSpatialIndex(srcLayer)
        # intersect = index.intersects(geomClip.boundingBox()) 
        # request = QgsFeatureRequest()
        # request.setFid(intersect)
        fids=[]
        # check real Intersecting
        countValidFeats=0
        countCandidateFeats=0
        for feature in cands: #layer.getFeatures(request):
            countCandidateFeats=countCandidateFeats + 1
            if geomClip.intersects(feature.geometry()):
                fids.append(feature.id())
                countValidFeats = countValidFeats + 1
        #print(countValidFeats,"von", countCandidateFeats, "schneiden Basislinie")
        
        
        featuresOnLine=srcLayer.getFeatures(fids)
        
        
        return featuresOnLine #return a list of features

    def punktEntfernung2D(self, position1, position2):
        deltaX=position2.x()-position1.x()
        deltaY=position2.y()-position1.y()
        s=math.sqrt(deltaX*deltaX+deltaY*deltaY)
        #print("distance",s, position1, position2)
        return s

    def richtungswinkelRAD(self, position1, position2):
        deltaX=position2.x()-position1.x()
        deltaY=position2.y()-position1.y()
        t1=-1
        #Wenn Beide Punkte identisch sind gibt es keinen Richtungswinkel
        if deltaX==0 and deltaY==0: 
            raise ValueError
        
        if deltaX==0 or deltaY==0:
            #Wenn DeltaX 0 ist zeigt die Richtung entweder nach Norden oder Süden
            if deltaX==0 and deltaY>0: #Nach Norden
                t1=0 
            else:                     #Nach Süden
                t1=math.pi

            #Wenn DeltaY 0 ist zeigt die Richtung entweder nach Westen oder Osten
            if deltaY==0 and deltaX>0: #nach Osten
                t1=math.pi/2
            else:                     #nach Westen
                t1=math.pi*1.5 
        else: 
            t1=math.atan(deltaX/deltaY)
            if deltaX>0 and deltaY>0:
                #I. Quadrant
                pass
            elif deltaX>0 and deltaY<0 or deltaX<0 and deltaY<0:
                t1=t1+math.pi
                #II. oder III. Quadrant
            elif deltaX<0 and deltaY>0:
                t1=t1+(2*math.pi)
                #IV. Quadrant
            else:
                print("Es konnte kein Quadrant für Richtungswinkel ermittelt werden")
                raise ValueError
        
        return t1

    #berechnet die Station und den Abstand eines Punktes zu einem Liniensegment
    def calcStationAbstandFromSegment(self, line, position):
        linePoints=line.asPolyline()
        p1=QgsGeometry.fromPoint(linePoints[0])
        p2=QgsGeometry.fromPoint(linePoints[1])
        #Richtungswinkel
        tSegment=richtungswinkelRAD(p1, p2)
        tToPosition=richtungswinkelRAD(p1, position)
        winkelP1Pos=tToPosition-tToPosition # Falls Winkeldifferenz winkelP1Pos negativ, liegt der Punkt links der Achse
        #polare Entferung von P1 zu Position
        polareStrecke=punktEntfernung2D(p1.asPoint(),position.asPoint())
        #Berechnung über Polarer Anhänger
        h=polareStrecke*math.sin(winkelP1Pos)
        q=polareStrecke*math.cos(winkelP1Pos)
        if h>0 and q>0: # Liegt der Lotpunkt auf dem Segment, sonst ist das Seqment in der Regel falsch
            return -1,-1
        else:
            return q,h #station, abstand


    # Erstellt eine lineare Referenzierung(QgsGeometry, QgsGeometry)
    def transformToLineCoords(self, position):
        stationBase=0
        minAbstand=99999
        curStation=0
        station=None
        for line  in self.lineSegments:
            stationSegment, abstand=self.transformToSegmentCoords(position, line)
            if not stationSegment is None and not abstand is None:
                curStation=stationBase + stationSegment
                #Es wird das Segment gesucht, welches den kuerzeten Abstand zum Punkt hat
                if stationBase==0:
                    minAbstand=math.fabs(abstand)
                    station=curStation
                elif math.fabs(abstand) < minAbstand:
                    minAbstand=math.fabs(abstand)
                    station=curStation
            stationBase = stationBase + line.length()
        return station, minAbstand
            
    # Erstellt eine lineare Referenzierung(QgsGeometry, QgsGeometry)    
    def transformToSegmentCoords(self, position, line):
        #teste Geometrytype
        #if position.wkbType()== and line.wkbType()==:
        
        station=None
        abstand=None
        linePoints=line.asPolyline() #ist ein Feld mit allen Punkten
        
        #Welche sind die beiden nächstgelegenen Punkte?
        min1=99999 #kürzeste Distanz
        min2=99999 #zweit-kürzeste Distanz
        dist=None
        laengeTemp=0
        stationNextPoint=0
        pktNum1=len(linePoints)+10
        pktNum2=len(linePoints)+11
        
        #3. Ansatz Analytische Geometrie --Schnittpunktzweier Geraden
        #print(linePoints)
        x1=linePoints[0].x()
        y1=linePoints[0].y()
        x2=linePoints[1].x()
        y2=linePoints[1].y()
        #print(x1,y1,x2,y2)
        #Punkt, der linear referenziert werden soll
        x3=position.x()
        y3=position.y()
        
        #Vector zwischen p1 und p2
        vec12=[x2-x1,y2-y1] 
        
        #Orthogonaler Vektor
        vecOrtho=[vec12[1],-vec12[0]] #x und y werden umgedreht und ein Vorzeichen vertauscht
        #print("vec12",vec12)
        #print("vecOrtho",vecOrtho)
        #Gerade 1 - linear equation 1
        #x  x1    vec12[0]
        # =   + t1*
        #y  y1    vec12[1]
        
        #Gerade 2 - linear equation 2
        #x  x3    vec12[1]
        # =   + t2*
        #y  y3    vec12[0]+(-1)

        #Aufstellung der Geradengleichung
        #Contruct the linear equation
        #print("x0",x1)
        #print("x1",vec12[0])
        #print("x2",x3)
        #print("x3",vec12[1])
        
        #fx=[x1, vec12[0], x3, vecOrtho[0]]      # *y[3]
        #fy=[y1, vec12[1], y3, vecOrtho[1]] # *(x[3])
        x=[x1, vec12[0], x3, vecOrtho[0]]      # *y[3]
        y=[y1, vec12[1], y3, vecOrtho[1]] # *(x[3])
        #print("x=",x)
        #print("y=",y)
        
        t1=self.getScaleGerade1AusGeradenGleichung(x,y)
        #print("t1=",t1)
        fx2=[x3, vecOrtho[0], x1, vec12[0]]      # *y[3]
        fy2=[y3, vecOrtho[1], y1, vec12[1]]
        #t2=self.getScaleGerade2AusGeradenGleichung(x,y)
        #print("t2=",t2)
        
        #Prüfung, ob Punkt zu Linienseqment gehört
        #Wenn t1 zwischen 0 und 1 liegt, dann befindet sich der Lotpunkt auf dem Linienstück zwischen P1 und P2
        #If the value of t1 is between 0 and 1, the intersection ist between the points 1 and 2
        if t1>-0.000001 and t1<1.000001: #
            pass
        else:
            #print("Punkt liegt nicht lotrecht auf Basislinie")
            return None, None
        
        
        #print("t1=",float(a1[1]), "/" , a1[0], "=",t1)
        #print("t1",t1)
        
        
        #Schnittpunkt
        # t1 wird in Geradengleichung eingesetzt
        xs=x1+t1*vec12[0]
        ys=y1+t1*vec12[1]
        #print "ys=",y2,"+",t1,"*",vec12[1]
        #print("Schnittpunkt", xs,ys)
        
        #xs2=x3+t2*vecOrtho[0]
        #ys2=y3+t2*vecOrtho[1]
        #print("Schnittpunkt2", xs2,ys2)
        
        vecOrthoReal=[]
        #delta x
        vecOrthoReal.append(x3-xs)
        #delta y
        vecOrthoReal.append(y3-ys)
        #Pythagroas
        sOrdinate=math.sqrt(vecOrthoReal[0]*vecOrthoReal[0]+vecOrthoReal[1]*vecOrthoReal[1])
        #Vorzeichen fuer Ordinate muss ermittelt werden
        winkelDiff=self.getRichtungsWinkelRADDiff(QgsPoint(x1,y1),QgsPoint(x2,y2),QgsPoint(x3,y3))
        if winkelDiff<0:
            ordinate=sOrdinate*-1
        else:
            ordinate=sOrdinate
        #Station auf Gerade
        #station on straight
        dx=xs-x1
        dy=ys-y1
        station=math.sqrt(dx*dx+dy*dy)
            
        return  station, ordinate
        #Betrag des Vektors zwischen dem Lotpunkt und P3 entspricht dem Abstand von der Achse(Ordinate)
        #t2=self.getScaleGerade2AusGeradenGleichung(x,y)
        
        #Function is part of 
    def getRichtungsWinkelRADDiff(self, p1,p2,p3):
        #Richtungswinkel von P1 nach P2
        t12=self.richtungswinkelRAD(p1,p2)
        t13=self.richtungswinkelRAD(p1,p3)
        winkelDiff=t13-t12
        return winkelDiff
        
        
    def getScaleGerade1AusGeradenGleichung(self, fx, fy):
        #Ausmultiplizieren der beiden Gleichungen
        xM=[]
        yM=[]
        for i in range(0,len(fx)):
            xM.append(fx[i]*fy[3])
            yM.append(fy[i]*fx[3])
        #print("xM", xM)
        #print "yM", yM
        
        #t2 muss sich wegkürzen
        #print("t2=0?",xM[3]+yM[3])
        if xM[3]+yM[3]!=0:
            for i in range(0,len(xM)):

                #Ändere ein Vorzeichen
                yM[i]=-1*yM[i]
        #print("yM", yM)
            
        #Additionsverfahren
        a=[]
        for i in range(len(xM)):
            a.append(xM[i]+yM[i])
            #print xM[i], "+", yM[i], "=", a[i]
        #print("a",a)
        a1=[]        
        #wenn t2 weggekürzt ist, löse nach t1 auf
        if a[3]==0:
            #alles außer t1 auf die Rechte Seite

            
            a1.append(a[1])
            a1.append(a[2]-a[0])
            #print("a1",a1)
        # a*t1=b -->t1=b/a
        #Division by zero
        if a1[0]==0:
            return None
        t1=float(a1[1])/a1[0]
        return t1
        
    def getScaleGerade2AusGeradenGleichung(self, fx, fy):
        #Ausmultiplizieren der beiden Gleichungen
        xM=[]
        yM=[]
        for i in range(0,len(fx)):
            xM.append(fx[i]*fy[3])
            yM.append(fy[i]*-fx[3])
        print("xM", xM)
        #print "yM", yM
        
        #t1 muss sich wegkürzen
        if xM[1]+yM[1]!=0:
            for i in range(0,len(xM)):

                #Ändere ein Vorzeichen
                yM[i]=-1*yM[i]
        print("yM", yM)
            
        #Additionsverfahren
        #a=[xy1, 0*t1, xy3, b*t2]
        #a: xy1 (+0*t1) = xy3 +b*t2
        #a: xy1-xy3 = b*t2 --> a1
        #a: (xy1-xy3)/b=t2
        a=[]
        for i in range(len(xM)):
            a.append(xM[i]+yM[i])
            #print xM[i], "+", yM[i], "=", a[i]
        print("a",a)
        
        #wenn t2 weggekürzt ist, löse nach t1 auf
        #a=[xy1, xy3, b*t2]
        a1=[]
        if a[1]==0:
            #alles außer t1 auf die Rechte Seite

            
            a1.append(a[3]) # b
            a1.append(a[0]-a[2]) #xy1-xy3
            print("a1",a1)
        #Division by zero
        if a1[0]==0:
            return None
        #t2=(xy1-xy3)/b
        t2=float(a1[1])/a1[0]
        return t2
        
        #1. Ansatz
        #Suche das Liniensegment, welches das kürzeste Lot hat
        minLot=inf #wird auf unendlich gesetzt
        #lote=[,] # kex-Value-Dictionary [Segment-id,Lotlänge]
        #prüfe ob ein Stützpunkt der Profilachse näher am Punkt liegt als das kürzeste Lot
            #entfernungen=[,] # kex-Value-Dictionary [Stützpunkt-id, Entfernung zum Punkt]
            #falls ja, entspricht der Lotpunkt genau dem am nächst gelegene StützPunkt und die Ordinate der berechneten Entfernung
            #-->Vorzeichen der Orinate muss hier noch ermittelt werden

        #2. Ansatz Es wird das Liniensegment gesucht, welches am nächten am Punkt liegt
        #QgsGeometry.closestSegmentWithContext()
        #Dazu werden die zwei am nächten gelegenen  zusammenhängenden Stützpunkte gesucht
        iVertex=0
        for vertex in linePoints:
            #Entfernung zwischen Stützpunkten und Abfragepunkt
            #if iVertex< doppelter Punkt am Linienende evtl weglassen
            dist=self.punktEntfernung2D(linePoints[iVertex],position.asPoint())
            if dist<min1: #ist es die bislang kürzete Distanz
                min2=min1 #min2 wird auf die zweit-kürzeste Distanz gesetzt
                min1=dist #min1 wird auf die kürzeste Distanz gesetzt
                pktNum1=iVertex
                #print "min gesetzt"
            elif dist<min2:#ist die bislang kürzete min2
                min2=dist #min2 wird auf die zweit-kürzeste Distanz gesetzt
                pktNum2=iVertex
            iVertex=iVertex+1
        
        #prüfe ob die beiden nächtgelegenden Punkt zusammen liegen
        if abs(pktNum2-pktNum1)>1:
            #Wenn der erste Stützpunkt der nächstgelgene ist, dann ist der muss der zweite StützPunkt verwendet werden 
            if pktNum1==0: 
                pktNum2=pktNum1+1
            #Wenn der letzte Stützpunkt der nächstgelgene ist, dann ist der muss der zweite StützPunkt verwendet werden 
            elif pktNum1==len(linePoints)-1:
                #setze ersten auf den vorletzen Stützpunkt
                pktNum1=len(linePoints)-2
                #setze zwiten auf den letzen Stützpunkt
                pktNum2=len(linePoints)-1
        
        #Berechne Station des nächstgelegenen Punktes
        print("pktNum1", pktNum1)
        stationNextPoint=0
        for i in range(0,pktNum1): #-1
            #print i, linePoints[i], linePoints[i+1]
            laengeTemp=self.punktEntfernung2D(linePoints[i], linePoints[i+1])
            stationNextPoint=stationNextPoint+laengeTemp

    ####### neuer Ansatz
        #Punkte des Liniensegmentes auf dem das Lot fällt
        p1=linePoints[pktNum1]
        p2=linePoints[pktNum2]
        p3=position.asPoint() # der zu Trassierende Punkt
        #subLinePoints.append(p1)
        #subLinePoints.append(p2)
        #Richtungswinkel
        tAchse=self.richtungswinkelRAD(p1,p2)
        tPosition=self.richtungswinkelRAD(p1,position.asPoint())
        winkelRAD=tPosition-tAchse
        #Schnittpunktberechnung mit senkrechter Gerade
        deltaX=p2.x()-p1.x()
        deltaY=p2.y()-p2.y()
        ax=(p3.x()-p1.x()-deltaX)/deltaX
        ay=(p1.y()+deltaY-p3.y())/deltaY
        
        print("ax", ax)
        print("ay", ay)
        
    ####### Ende neuer Ansatz

        #Berechnung Richtungswinkeldifferenzen
        t0_1=None
        t1_2=None
        t0_p=None
        t1_p=None
        winkelRAD=None
        subLinePoints=[]
        if pktNum1>len(linePoints)-2:
            pass
        elif pktNum1==len(linePoints)-2:
            #Punkt gehört zu letztem Segment
            subLinePoints.append(linePoints[len(linePoints)-2])
            subLinePoints.append(linePoints[len(linePoints)-1])
            
            t1_2=self.richtungswinkelRAD(linePoints[pktNum1],linePoints[pktNum1+1])
            t1_p=self.richtungswinkelRAD(linePoints[pktNum1],position.asPoint())
            winkelRAD=t1_p-t1_2
            bolStatNachNextVertex=False #liegt auf jeden Fall davor
        elif pktNum1==0:
            #Punkt gehört zu erstem Segment
            subLinePoints.append(linePoints[0])
            subLinePoints.append(linePoints[1])
            
            t0_1=self.richtungswinkelRAD(linePoints[pktNum1],linePoints[pktNum1+1])
            t0_p=self.richtungswinkelRAD(linePoints[pktNum1],position.asPoint())
            winkelRAD=t0_p-t0_1
            bolStatNachNextVertex=True#liegt auf jeden Fall dahinter
        else:
            #Punkt liegt dazwischen
            t0_1=self.richtungswinkelRAD(linePoints[pktNum1-1],linePoints[pktNum1])
            t0_p=self.richtungswinkelRAD(linePoints[pktNum1-1],position.asPoint())

            t1_2=self.richtungswinkelRAD(linePoints[pktNum1],linePoints[pktNum1+1])
            t1_p=self.richtungswinkelRAD(linePoints[pktNum1],position.asPoint())
            
            deltaT1=t0_p-t0_1
            deltaT2=t1_p-t1_2
            if deltaT2 < (math.pi/2) and deltaT2 > -(math.pi/2):
                #Punkt gehört zu nachfolgendem segment
                subLinePoints.append(linePoints[pktNum1])
                subLinePoints.append(linePoints[pktNum1+1])

                winkelRAD=t1_p-t1_2
                bolStatNachNextVertex=true
            else:
                #Punkt gehört zu Vorgänger-segment
                subLinePoints.append(linePoints[pktNum1-1])
                subLinePoints.append(linePoints[pktNum1])
                
                winkelRAD=t0_p-t0_1
                bolStatNachNextVertex=False
        subLine=QgsGeometry.fromPolyline(subLinePoints)
        polareStrecke=self.punktEntfernung2D(subLine.vertexAt(0),position.asPoint())
        #Berechnung über Polarer Anhänger
        h=polareStrecke * math.sin(winkelRAD)
        q=polareStrecke * math.cos(winkelRAD) 
        if bolStatNachNextVertex==False:
            #Punkt gehört zu Vorgänger-segment
            
            p=subLine.length()-q #Höhensatz des Dreieckes (h²=p*q)
            stationLotPoint=stationNextPoint-p

        else:
            stationLotPoint=stationNextPoint+q
        
        
        if stationLotPoint > 0 and stationLotPoint<line.length():
            station=stationLotPoint
            abstand=h
            return station, abstand
        else:
            print("Station und Abstand konnte nicht aus Koordinaten ermittelt werden!", "Punkt liegt außerhalb der Abschnittsgeometrie!")
            return None

    def getIntersectionPointofPolyLine(self, line1):
        pointList=[]
        stations=[]
        baseStation=0
        anyPoint=False
        i=0
        for segmentAufProfil in self.lineSegments:
            pt, stationOnSegment = self.getIntersectionPointofSegment(line1, segmentAufProfil)
            #print(pt, stationOnSegment)
            if not pt is None and not stationOnSegment is None:
                #print("Test2", pt.asWkt(), stationOnSegment)
                anyPoint=True
                curStation=baseStation + stationOnSegment
                pointList.append(pt)
                stations.append(curStation)
                #if baseStation < 37000 and baseStation > 0:
                #    print("Schnittpunkt", pt.asWkt(), baseStation, stationOnSegment, curStation)

            baseStation=baseStation + segmentAufProfil.length()
            i=i+1
        #print(i, "Segmente auf der Basislinie auf Schnittpunkte durchsucht")
        if anyPoint:
            return pointList, stations #QgsPoint(), float()
        else:
            return None, None
        

    def getIntersectionPointofSegment(self, baseLine, line2): #BaseLine ist die Linie auf der die Station angebeben werden soll

        station=None

        baseLinePoints=baseLine.asPolyline()
        linePoints=line2.asPolyline() #ist ein Feld mit allen Punkten
        
       
        #3. Ansatz Analytische Geometrie --Schnittpunktzweier Geraden
        #print(linePoints)
        x1=baseLinePoints[0].x()
        y1=baseLinePoints[0].y()
        x2=baseLinePoints[1].x()
        y2=baseLinePoints[1].y()
        #print(x1,y1,x2,y2)
        #Linie, deren Schnitt gesucht wird
        x3=linePoints[0].x()
        y3=linePoints[0].y()
        x4=linePoints[1].x()
        y4=linePoints[1].y()        
        #Vector zwischen p1 und p2
        vec12=[x2-x1,y2-y1] 
        
        #Orthogonaler Vektor
        vec34=[x4-x3,y4-y3] #x und y werden umgedreht und ein Vorzeichen vertauscht
        #print("vec12",vec12)
        #print("vecOrtho",vecOrtho)
        #Gerade 1 - linear equation 1
        #x  x1    vec12[0]
        # =   + t1*
        #y  y1    vec12[1]
        
        #Gerade 2 - linear equation 2
        #x  x3    vec12[1]
        # =   + t2*
        #y  y3    vec12[0]+(-1)

        #Aufstellung der Geradengleichung
        #Contruct the linear equation
        #print("x0",x1)
        #print("x1",vec12[0])
        #print("x2",x3)
        #print("x3",vec12[1])
        
        #fx=[x1, vec12[0], x3, vecOrtho[0]]      # *y[3]
        #fy=[y1, vec12[1], y3, vecOrtho[1]] # *(x[3])
        x=[x1, vec12[0], x3, vec34[0]]      # *y[3]
        y=[y1, vec12[1], y3, vec34[1]] # *(x[3])
        #print("x=",x)
        #print("y=",y)
        
        t1=self.getScaleGerade1AusGeradenGleichung(x,y)
        #print("t1=",t1)
        fx2=[x3, vec34[0], x1, vec12[0]]      # *y[3]
        fy2=[y3, vec34[1], y1, vec12[1]]
        t2=self.getScaleGerade1AusGeradenGleichung(fx2,fy2)
        #print("t2=",t2)
        
        #Prüfung, ob Punkt zu Linienseqment gehört
        #Wenn t1 zwischen 0 und 1 liegt, dann befindet sich der Lotpunkt auf dem Linienstück zwischen P1 und P2
        #If the value of t1 is between 0 and 1, the intersection ist between the points 1 and 2
        if t1>-0.000001 and t1<1.000001: #
            pass
        else:
            #print("Punkt liegt nicht lotrecht auf Basislinie")
            return None, None
        
        
        #print("t1=",float(a1[1]), "/" , a1[0], "=",t1)
        #print("t1",t1)
        
        
        #Schnittpunkt
        # t1 wird in Geradengleichung eingesetzt
        xs=x1+t1*vec12[0]
        ys=y1+t1*vec12[1]
        #print "ys=",y2,"+",t1,"*",vec12[1]
        #print("Schnittpunkt", xs,ys)
        
        xs2=x3+t2*vec34[0]
        ys2=y3+t2*vec34[1]
        #print("Schnittpunkt2", xs2,ys2)
        

        #Station auf Gerade(der 2. Linie--hier ProfilLinie)
        #station on straight
        #print(QgsPointXY(x1,y1),QgsPointXY(xs,ys))
        dx=xs-x3
        dy=ys-y3
        station=math.sqrt(dx*dx+dy*dy)
        #print("Station:",station)
            
        return  QgsGeometry.fromPointXY(QgsPointXY(xs,ys)), station

    def verdichtePunkte(self, dichte):
        newLinePoints=[]
        lastVertex=None
        for line in self.lineSegments:
            p1=line.vertexAt(0)
            p2=line.vertexAt(1)
            firstPt=p1
            newLinePoints.append(firstPt)
            #newLinePoints.append(QgsGeometry.fromPointXY(QgsPoint(p1x, p1y)))

            lastVertex=p2
            #Entfernung zwischen P1 und P2
            s12=self.punktEntfernung2D(p1, p2)
            #Solange Entfernung groesser als Dichte, setze Zwischenpunkte
            curLength=0
            #Aktueller neuer Stuetzpunkt
            curX=p1.x()
            curY=p1.y()
            while curLength < s12:
                #Vektor p1-p2
                dx=p2.x()-p1.x()
                dy=p2.y()-p1.y()
                #Dreisatz
                dxs=dx * dichte / s12
                dys=dy * dichte / s12
                xs=curX+dxs
                ys=curY+dys
                #print(dx, dy, xs, ys)
                

                #Fuege neuen Stuetzpunkt hinzu
                
                newLinePoints.append(QgsPoint(xs, ys))

                #Aktueller Stuetzpunkt wir weitergezaehlt
                curX=xs
                curY=ys
                curLength=curLength + dichte
            
        #Fuege letzen Stuetzpunkt der Polyline hinzu
        newLinePoints.append(lastVertex)
        
        fineLine=QgsGeometry.fromPolyline(newLinePoints)
        # print("Linienverdichtung")
        # for p in newLinePoints:
            # print(p.asWkt())
        return fineLine

def isLineType(vectorLayer):
    if vectorLayer.wkbType()==2 or vectorLayer.wkbType()==1002 or vectorLayer.wkbType()==2002 or vectorLayer.wkbType()==3002 or vectorLayer.wkbType()==5 or vectorLayer.wkbType()==1005 or vectorLayer.wkbType()==2005 or vectorLayer.wkbType()==3005:
        return True
    else:
        return False

#extraiere Linienseqmente
def extractLineSegments( geom):
    points=getVertices(geom)
    #create the lines
    lines=[]
    i=0 # Line number
    while i < len(points)-1:
        p1=points[i]
        p2=points[i+1]
        lineGeom=QgsGeometry.fromPolyline([p1,p2])
        lines.append(lineGeom)
        i=i+1
    return lines        

#liefert die Stuetzpunkte einer Single-Geometrie
def getVertices(geom):
    v_iter = geom.vertices()
    points=[]

    while v_iter.hasNext():
        pt = v_iter.next()
        points.append(pt)
        #print(pt.x(), pt.y())
    return points       

def getSchnittpunkteAusLinien(overlapFeats, laengsProfil):
    #linesOfProfil = self.extractLineSegments(self.laengsProfil.srcProfilLine)
    schnittpunktFeatures=[]
    ioFeat=0
    countPoints=0
    for feat in overlapFeats:
        #Feature bekommr neues Attribut Station
        if ioFeat==0:
            fields=feat.fields()
            fields.append(QgsField("station", QVariant.Double))
        
        #check if Multipolygon
        if feat.geometry().isMultipart: #feat.geometry().wkbType()==5 or feat.geometry().wkbType()==1005 or feat.geometry().wkbType()==2005 or feat.geometry().wkbType()==3005:
            #for polygon in feat:  ############## Achtung normalerweise wird diese Schleife zum Auflösen des Multiparts benoetigt
            #    print(type(polygon))
            linesOfPolygon = extractLineSegments(feat.geometry())#polygon)
            #print("Polyline", len(linesOfPolygon),"Segments")
            intersections = {}
            
            for lineP in linesOfPolygon:
                #hole alle Schnittpunkte
                #print("Test1", self.laengsProfil.linearRef.profilLine3d.asWkt())
                intersectionPoints, stations=laengsProfil.linearRef.getIntersectionPointofPolyLine(lineP)
                if not intersectionPoints is None:
                    #zaehle Schnittpunkte
                    countPoints=countPoints+len(intersectionPoints)
                    if not intersectionPoints is None:
                        for i in range(len(intersectionPoints)):
                            intersections[stations[i]]=intersectionPoints[i]
                            pt=intersectionPoints[i].asPoint()
                            #print(pt.x(), pt.y())
                            
                            schnittPunktFeat=QgsFeature(feat)#Copy of the Feature
                            schnittPunktFeat.setGeometry(intersectionPoints[i])
                            attrs=feat.attributes()
                            attrs.append(stations[i]) # station wird in Attributen gespeichert
                            schnittPunktFeat.setAttributes(feat.attributes())                               
                            schnittpunktFeatures.append(schnittPunktFeat)
        
        else: # other geometry type
            linesOfPolygon = extractLineSegments(feat.geometry())
        ioFeat=ioFeat+1
    print("Schneidende Linien",ioFeat,"Schnittpunkte:", countPoints)
    return schnittpunktFeatures

######################################
# hole Layer
layers=[layer for layer in QgsProject.instance().mapLayers().values()]

baseLineLayer=layers[5]# 0]
print("baseLine:", baseLineLayer.name())
#vectorLayer1=layers[8]#Bohrungen 1]
#print("vectorLayer1:", vectorLayer1.name())
#vectorLayer2=layers[13]#gk25Flaechen 3]
#print("vectorLayer2:", vectorLayer2.name())
lineLayer=layers[15]#gk25Linien
print("lineLayer:", lineLayer.name())
rasterLayer=layers[11]#2]
print("rasterLayer:", rasterLayer.name())
ueberhoehung=10
baseLine=None

#Basline Layer must have only 1 Feature
if baseLineLayer.featureCount()==1:
#baseLine must be the first feature
    baseLine=baseLineLayer.getFeature(0).geometry()       
elif len(baseLineLayer.selectedFeatures())==1:
    selection=baseLineLayer.selectedFeatures()
    #baseLine must be the first feature
    baseLine=selection[0].geometry() 
else:
    print("BaseLine layer needs exactly one line feature! ", baseLineLayer.featureCount(), "Just select one feature!")
    raise QgsProcessingException("BaseLine layer needs exactly one line feature: "+str(baseLineLayer.featureCount())+ " Just select one feature!")
        #take CRS from Rasterlayer 
crsProfil=rasterLayer.crs()    
#check if layers have the same crs
if not baseLineLayer.crs().authid()==rasterLayer.crs().authid():
    # if not, transform to raster crs()
    trafo1=QgsCoordinateTransform(baseLineLayer.crs(),rasterLayer.crs(),QgsProject.instance())
    #transform BaseLine
    opResult1=baseLine.transform(trafo1,QgsCoordinateTransform.ForwardTransform, False)
if not lineLayer.crs().authid()==rasterLayer.crs().authid():
    # if not, transform to raster crs()
    trafo2=QgsCoordinateTransform(lineLayer.crs(),rasterLayer.crs(),QgsProject.instance())
    #transform BaseLine
    opResult2=baseLine.transform(trafo2,QgsCoordinateTransform.ForwardTransform, False)

layerZFieldId=-1
#print("init Terrain")

tm = TerrainModel(rasterLayer)
#print("init LaengsProfil")
lp = LaengsProfil(baseLine, tm)

#(sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
#context, lineLayer.fields(), lineLayer.wkbType(), crsProfil)
try:
    total = 100.0 / len(lp.linearRef.lineSegments)
except:
    raise QgsProcessingException("Keine Basislinie")
print("get Kandidaten")

bufferWidth=10 #10 m
#ermittle Kanditaten featuresOnLine=[]
featuresOnLine=lp.linearRef.getFeaturesOnBaseLine(lineLayer, bufferWidth)
#Falls Linien oder Polygone, dann ermittle Schnittpunkte mit Laengsprofil
print("Erzeuge Schnittpunkt-Features")
#Erzeuge Schnittpunkt-Features
schnittpunkte=[] #Liste von Features
if isLineType(lineLayer):
    print("isLineType")
    schnittpunkte=getSchnittpunkteAusLinien(featuresOnLine, lp) #Um Attribute der geschnittenen Objekte zu uebernehmen, muss hier mehr uebergeben werden
    
    
    #Berechne Z-Werte
    featuresWithZ=tm.addZtoPointFeatures(schnittpunkte,layerZFieldId)
    
    #Erzeuge Profilgeometrien gehr derzeit nur als Punkt
    profilFeatures=[]
    for current, srcFeat in enumerate(featuresWithZ):
        # Stop the algorithm if cancel button has been clicked
        # if feedback.isCanceled():
            # break
        srcGeom=srcFeat.geometry()
        #print("pointsWithZ", srcFeat.attributes(), srcGeom.asWkt())
        profilGeometries=lp.extractProfilGeom(srcGeom, ueberhoehung, lp.srcProfilLine)
        for profilGeom in profilGeometries:
            profilFeat = QgsFeature(lineLayer.fields())   
            #muss fuer jeden Geometrityp gehen
            profilFeat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(profilGeom.x(),profilGeom.y())))
            profilFeat.setAttributes(srcFeat.attributes())
            #print("ProfilFeature",srcFeat.attributes(),profilGeom.asWkt())

        # Add a feature in the sink
        print(profilFeat.attributes())
        profilFeatures.append(profilFeat)
        #sink.addFeature(profilFeat, QgsFeatureSink.FastInsert)
        # Update the progress bar
        #feedback.setProgress(int(current * total))

# create layer
profilLayer= QgsVectorLayer("Point", lineLayer.name()+"_profil", "memory")
pr = profilLayer.dataProvider()

# add fields
pr.addAttributes(lineLayer.fields())
# pr.addAttributes([QgsField("name", QVariant.String),
                    # QgsField("age",  QVariant.Int),
                    # QgsField("size", QVariant.Double)])
profilLayer.updateFields() # tell the vector layer to fetch changes from the provider

pr.addFeatures(profilFeatures)
        
layerTree = QgsProject.instance().layerTreeRoot()
shapeGroup = layerTree.addGroup("ProfilLayer "+str(ueberhoehung)+"-fach ueberhoeht")
#QgsProject.instance().addMapLayer(ls.profilLayers[0])
#QgsProject.instance().addMapLayer(ls.profilLayers[1])
#for layer in ls.profilLayers:
shapeGroup.addLayer(profilLayer)