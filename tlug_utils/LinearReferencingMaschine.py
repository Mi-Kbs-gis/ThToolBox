# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TlugProcessing
                                 LinearReferencingMaschine
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
__date__ = '2019-01-18'
__copyright__ = '(C) 2019 by Michael Kürbs by Thüringer Landesamt für Umwelt, Bergbau und Naturschutz (TLUBN)'

from qgis.core import *
from qgis.PyQt.QtCore import QObject
import math

class LinearReferencingMaschine(QObject):
    
    def __init__(self, profilLine, crs, feedback): #QgsVectorLayer, QgsLinestringZ
        self.feedback=feedback
        self.profilLine=profilLine
        self.crs=crs
        #self.profilLine3d
        self.lineSegments=self.extractLineSegments(profilLine)
        self.isSimpleLine=self.isA2PointLineString(profilLine)
    
    def isA2PointLineString(self, geom):
        points=[vertex for vertex in geom.vertices()]
        if len(points)==2:
            return True
        else:
            return False
        
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
        
    def getFeaturesOnBaseLine(self, srcLayer, bufferWidth): # works with QgsVectorlayer
        #self.feedback.pushInfo("getFeaturesOnBaseLine")
        positionsOnLine=[]
        geomClip=self.profilLine.buffer(bufferWidth,1)
        # if crs difterent, transform clipping geometry to srcLayer crs
        if not srcLayer.crs().authid()==self.crs.authid():
            trafo=QgsCoordinateTransform(srcLayer.crs(),self.crs, QgsProject.instance())
            #transform clipGeom to SrcLayer.crs Reverse
            geomClip.transform(trafo,QgsCoordinateTransform.ReverseTransform, False)
        #self.feedback.pushInfo("1geomClip: "+ str(geomClip.asWkt()))
        #QgsFeatureRequest liefert alle Punkte, die zur Linie gehoeren
        #QgsFeatureRequest wird im srcLayer.crs() durchgeführt
        index=None
        try:
            index = QgsSpatialIndex(srcLayer.getFeatures())
        except:
            msg="Input layer feature count is too big! Try to use it with a selection!"
            feedback.reportError(msg)
            raise QgsProcessingException(msg)
            
        intersect = index.intersects(geomClip.boundingBox())
        cands = srcLayer.getFeatures(intersect)



        #cands = srcLayer.getFeatures(QgsFeatureRequest().setFilterRect(geomClip.boundingBox()))
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
            #self.feedback.pushInfo("2geomClip: "+ str(geomClip.asWkt())+" with "+str(feature.geometry().asWkt()))
            countCandidateFeats=countCandidateFeats + 1
            if geomClip.intersects(feature.geometry()):
                #self.feedback.pushInfo("FeatureOnBaseLine: "+ feature.geometry().asWkt())
                fids.append(feature.id())
                countValidFeats = countValidFeats + 1
        self.feedback.pushInfo(str(countValidFeats) + " von "+str(countCandidateFeats)+ " schneiden Basislinie")
        
        
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
                    minAbstand=abstand
                    station=curStation
                elif math.fabs(abstand) < math.fabs(minAbstand): #compare just absolute values
                    minAbstand = abstand
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
        vecOrtho=[-vec12[1],vec12[0]] #x und y werden umgedreht und das Vorzeichen des x-Wertes vertauscht->Rechtssystem
        #das Vorzeichen von t2 zeigt auf welcher Seite der Punkt liegt (+/Rechts , -/links)
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

        t2=self.getScaleGerade1AusGeradenGleichung(fx2,fy2)
        #das Vorzeichen von t2 zeigt auf welcher Seite der Punkt liegt (+/Rechts , -/links)

        #t2=self.getScaleGerade2AusGeradenGleichung(x,y)
        #print("t2=",t2)
        
        #Prüfung, ob Punkt zu Linienseqment gehört
        #Wenn t1 zwischen 0 und 1 liegt, dann befindet sich der Lotpunkt auf dem Linienstück zwischen P1 und P2
        #If the value of t1 is between 0 and 1, the intersection ist between the points 1 and 2
        if t1>-0.000001 and t1<1.000001: #
            pass
        elif self.isSimpleLine==False: # Wenn Punkt außerhalb des Linensegments liegt und die Achse mehrere Stützpunkte hat, abbrechen
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
        #Betrag des orthogonalen vektors / Absolute of orthogonal vector
        absVecOrtho=math.sqrt(vecOrtho[0]*vecOrtho[0]+vecOrtho[1]*vecOrtho[1])
        #das Vorzeichen von t2 zeigt auf welcher Seite der Punkt liegt (+/Rechts , -/links)
        ordinate= t2 * absVecOrtho

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

    def getIntersectionPointsofPolyLine(self, line1):
        pointList=[]
        stations=[]
        baseStation=0
        anyPoint=False
        i=0
        for linRefSegment in self.lineSegments: #iterate all seqments of the baseLine, it can included breakpoints
            #look for an intersection for each line seqmenent of the baseline
            pt, stationOnSegment = self.getIntersectionPointofSegment(line1, linRefSegment)
            if not pt is None and not stationOnSegment is None:
                #self.feedback.pushInfo("pt,Station: " + str(pt) + " " + str(stationOnSegment))
                anyPoint=True
                curStation=baseStation + stationOnSegment
                pointList.append(pt)
                stations.append(curStation)
                #if baseStation < 37000 and baseStation > 0:
                #self.feedback.pushInfo("Schnittpunkt"+"\t"+ pt.asWkt()+"\t"+  str(baseStation)+"\t"+  str(stationOnSegment)+"\t"+  str(curStation))

            baseStation=baseStation + linRefSegment.length()
            i=i+1
        #print(i, "Segmente auf der Basislinie auf Schnittpunkte durchsucht")
        if anyPoint:

            return pointList, stations #QgsPoint(), float()
        else:
            return None, None
        
    # gets the intersection point of two line seqments
    def getIntersectionPointofSegment(self, baseLine, line2): #BaseLine ist die Linie auf der die Station angebeben werden soll

        station=None

        baseLinePoints=baseLine.asPolyline()
        linePoints=line2.asPolyline() #ist ein Feld mit allen Punkten
        #self.feedback.pushInfo( "Baseline " + str(baseLinePoints))
        #self.feedback.pushInfo( "schnittLine " + str(linePoints))
       
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
        #self.feedback.pushInfo( "t1=" + str(t1) + " t2:" + str(t2) )
        #Prüfung, ob Punkt zu Linienseqment gehört
        #Wenn t1 zwischen 0 und 1 liegt, dann befindet sich der Lotpunkt auf dem Linienstück zwischen P1 und P2
        #If the value of t1 is between 0 and 1, the intersection ist between the points 1 and 2
        if t1 is None or t2 is None:
            return None, None
            # no intersection
        elif t1>-0.000001 and t1<1.000001 and t2>-0.000001 and t2<1.000001: #
            #self.feedback.pushInfo("t2: "+str(t2)+" t1: " + str(t1) + " " + str(baseLine))
            pass
        elif self.isSimpleLine==False:  # Wenn Punkt außerhalb des Linensegments liegt und die Achse mehrere Stützpunkte hat, abbrechen
            
            # no intersection
            
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
        #self.feedback.pushInfo("Intersection: " + str(xs) + " " + str(ys))
        return  QgsGeometry.fromPointXY(QgsPointXY(xs,ys)), station

    def verdichtePunkte(self, dichte): # Dichte in meter
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
            #Solange Entfernung groesser als die DOPPELTE DICHTE, setze Zwischenpunkte
            curLength=0
            #Aktueller neuer Stuetzpunkt
            curX=p1.x()
            curY=p1.y()
            while (curLength + dichte) < s12:
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
        #self.feedback.pushInfo("Linienverdichtung: " + str(fineLine.asWkt()))
        return fineLine

    def linePartsByStation(self, polygon, listPointStationId):
        for ptStat in listPointStationId:
            ptGeom = ptStat[0]
            ptStation = ptStat[1]
            curStation = 0
            for line in self.lineSegments:
                # Erster und Letzter Punkt der Linie wird benötigt wenn len(listPointStationId)==1
                if len(listPointStationId)==1:
                    pass
                if (curStation + line.length()) > ptStation:
                    pass
                
                #zähle station aufwärts
                curStation=curStation + line.length()
                
    def transformProfileFeatureToRealWorld(self, feature, featCrs, feedback, abstand=0, zFactor=1):
        trafo=QgsCoordinateTransform(featCrs, self.crs, QgsProject.instance())
        srcGeom = feature.geometry()
        #check Projection, transform if different
        if not featCrs.authid() == self.crs.authid():
            srcGeom.transform(trafo,QgsCoordinateTransform.ForwardTransform, False)
        

        rwFeat=QgsFeature( feature )
        realWorldGeom = None
        

        #check GeomType
        if "Point" in srcGeom.asWkt():
            if srcGeom.isMultipart():
                multiGeom = srcGeom.asMultiPolyline()
                rwGeoms=[]
                realWorldGeom = QgsGeometry()
                for i in multiGeom:
                    pxy=i.asPoint()
                    rwPoint3D=self.pointToRealWorld( pxy, abstand, zFactor ) #QgsPoint() -->PointZ
                    rwGeoms.append( QgsGeometry().fromWkt( rwPoint3D.asWkt() ) )
                    realWorldGeom.addPart(rwPoint3D)
                #realWorldGeom = QgsGeometry().fromPoint(rwGeoms)
            else:
                rwPoint3D=self.pointToRealWorld( srcGeom.asPoint(), abstand, zFactor )
                realWorldGeom = QgsGeometry().fromWkt(rwPoint3D.asWkt())
        elif "Line" in srcGeom.asWkt():
            if srcGeom.isMultipart():
                multiGeom = srcGeom.asMultiPolyline()
                realWorldGeom = QgsGeometry()
                rwGeoms=[]
                i=0
                for iGeom in multiGeom:
                    rwPoints=[]
                    for pxy in iGeom:
                        rwPoint3D=self.pointToRealWorld( pxy, abstand, zFactor )
                        rwPoints.append( rwPoint3D )
                    rwGeoms.append(QgsGeometry().fromPolyline(rwPoints))
                    if i==0:
                        realWorldGeom = QgsGeometry().fromPolyline(rwPoints)
                    else:
                        realWorldGeom.addPart( QgsGeometry().fromPolyline(rwPoints) )
                    i=i+1
            else:
                rwPoints=[]
                for pxy in srcGeom.asPolyline():
                    pxy
                    rwPoint3D=self.pointToRealWorld( pxy, abstand, zFactor )
                    rwPoints.append( rwPoint3D )
                realWorldGeom = QgsGeometry().fromPolyline(rwPoints)
        elif "Polygon" in srcGeom.asWkt():
        
            if srcGeom.isMultipart():
                realWorldGeom=QgsGeometry()
                polygons=[]
                zPolyLines=[]
                multiGeom = srcGeom.asMultiPolygon()
                for i, geom in enumerate(multiGeom):
                    for j, pxyList in enumerate(geom):
                        rwPoints=[]
                        for pxy in pxyList:
                            rwPoint3D=self.pointToRealWorld( pxy, abstand, zFactor )
                            rwPoints.append( rwPoint3D )
                        polygons.append( rwPoints )
                        zPolyLines.append( QgsGeometry().fromPolyline( rwPoints ) )
                realWorldGeom=QgsGeometry()
                wktMPZ=""
                for ir, ring in enumerate(zPolyLines):
                    wkt=ring.asWkt()
                    wkt=wkt.replace('LineStringZ (', "PolygonZ ((")
                    wkt=wkt.replace(")", "))")
                    polygonZ = QgsGeometry().fromWkt(wkt)
                    if ir == 0:
                        wkt1=polygonZ.asWkt()
                        wkt1=wkt1.replace("PolygonZ ((", "MultiPolygonZ (((")
                        wktMPZ=wktMPZ + wkt1
                        
                    else:
                        wktI=polygonZ.asWkt()
                        wktI=wktI.replace("PolygonZ ((", ", ((") #GeommetryTypName wird durch Komma ersetzt
                        wktMPZ=wktMPZ + wktI
                        
                wktMPZ=wktMPZ+")" #Dritte Klammer
                #self.feedback.pushInfo( "PolygonZ: " + wktMPZ )
                realWorldGeom = QgsGeometry().fromWkt( wktMPZ )
                    
            else:
                rwPoints=[]
                for pxy in srcGeom.vertices():
                    rwPoint3D=self.pointToRealWorld( pxy, abstand, zFactor )
                    rwPoints.append( rwPoint3D )
                realWorldPolyLineZ = QgsGeometry().fromPolyline(rwPoints)
                wkt=realWorldPolyLineZ.asWkt()
                wkt=wkt.replace('LineStringZ (', "PolygonZ ((")
                wkt=wkt.replace(")", "))")
                #feedback.pushInfo(wkt)
                realWorldGeom=QgsGeometry().fromWkt(wkt)
        else:
            msg = "Unknown Geometry Type: " + str( srcGeom.asWkt() )
            feedback.reportError(msg)
            raise QgsProcessingException(msg)
        
        #create Feature
        if not realWorldGeom is None:
            rwFeat.setGeometry(realWorldGeom)
            rwFeat.setAttributes(feature.attributes())
            #feedback.pushInfo( realWorldGeom.asWkt() )
            return rwFeat
        else:
            msg = "Error transformProfileFeatureToRealWorld: " + str( feature ) + " Geom: " +  feature.geometry().asWkt()
            feedback.reportError(msg)
            raise QgsProcessingException(msg)

    def pointToRealWorld(self, profilPoint, abstand, zFactor):
        z = profilPoint.y() / zFactor # Reverse Calculation Z-Factor / Überhöhung
        station = profilPoint.x()
        realWorldPt2D = self.lineCoordsToPosition( station, abstand )
        realWorldPt3D = QgsPoint( realWorldPt2D.x(), realWorldPt2D.y(), z)
        #self.feedback.pushInfo("RWPt: " + realWorldPt3D.asWkt())
        return realWorldPt3D
        
    def lineCoordsToPosition(self, station, abstand):
        curStation=0
        pRW = None
        for line in self.lineSegments:
            if not pRW is None:
                break

            #is point an this segment
            isOnSegment=False
            if round(station, 3) < round(curStation + line.length(),3) and round(station,3) > round(curStation,3):
                isOnSegment=True


            if self.isSimpleLine==True or isOnSegment==True:
                p1 = line.vertexAt(0)         
                p2 = line.vertexAt(1) 
                #Deltas 1->2
                dx = p2.x() - p1.x()
                dy = p2.y() - p1.y()
                
                stationOnLine = station - curStation
                
                t1Factor = stationOnLine / line.length()
                if abstand==0:
                    # Point in Real World Coordinates
                    dxi = dx * t1Factor
                    dyi = dy * t1Factor
                    xRW = p1.x() + dxi
                    yRW = p1.y() + dyi
                    pRW = QgsPointXY( xRW, yRW )
                else:
                    t2Factor = math.fabs( abstand ) / line.length()
                    #Richtungsvektor vom Lotpunkt zum Punkt
                    dxOrtho = None
                    dyOrtho = None
                    if abstand > 0:
                        dxOrtho = dy
                        dyOrtho = - dx #Linkssystem
                    else:
                        dxOrtho = -dy #Rechtssystem
                        dyOrtho = dx
                    #Addition of 2 vectors
                    xRW = p1.x() + ( dx * t1Factor ) + dxOrtho * t2Factor
                    yRW = p1.y() + ( dy * t1Factor ) + dyOrtho * t2Factor
                    pRW = QgsPointXY( xRW, yRW ) 
            elif round(station, 3) == round(curStation,3): # If it is exactly the baseLine-Vertex
                p1 = line.vertexAt(0)
                pRW = QgsPointXY( p1.x(), p1.y() ) 
            elif round(station, 3) == round(self.profilLine.length(),3): # If it is exactly the baseLine-End-Vertex
                line=self.lineSegments[ len( self.lineSegments ) - 1 ]
                p1 = line.vertexAt(1)
                pRW = QgsPointXY( p1.x(), p1.y() ) 
            

            curStation=curStation + line.length()

            
        if pRW == None:
            msg = "Error lineCoordsToPosition: Station: " + str( station ) + "<--> BaseLineLength: " +  str( self.profilLine.length() ) 
            self.feedback.reportError(msg)
            raise QgsProcessingException(msg)
        
        return pRW # Point in Real World Coordinates

        
    