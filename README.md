# ThToolBox at master


## QGIS Processing Toolbox of Thüringer Landesamt für Umwelt, Bergbau und Naturschutz (TLUBN)
### 2D -> 3D

#### Attach raster values to line vertices
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/AttachZvalOnLine_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/AttachZvalOnLine_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/AttachZvalOnLine_Logo.png" style="max-width:100%;"></a></p>
````
Process transform a LineString to LineStringZ geometry.
Two modes available
Mode "only vertices" sets Z-Values to given line vertices based on a (1 Band) raster data source.
Mode "fill by raster resolution" sets Z-Values to given line vertices and fill additional vertices based on the resolution of the raster layer.
````

### File Tools

#### Files To Table
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/Files2Table_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/Files2Table_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/Files2Table_Logo.png" style="max-width:100%;"></a></p>
````
Returns a table with entrys for each file in a directory. 
Include some file properties.
````

### To Profile Coordinates (Cross Section)
```
Geometrys would be transformed to a linear referencing by a baseline.
```
#### Raster Gradient
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_Gradient_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_Gradient_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_Gradient_Logo.png" style="max-width:100%;"></a></p>
````
Transforms a single Line to profile coordinates with considering of elevation.
On Raster NoDATA-Values, the profile elevation where set to 0.
Select a line feature or use an one feature layer as Baseline.
````
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_LineIntersection_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_LineIntersection_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_LineIntersection_Logo.png" style="max-width:100%;"></a></p>
<p>Line - Baseline Intersections</p>
<ol>
li>Get the intersections from a line layer with the baseline and transform them to profile coordinates.</li>
li>Select a line feature or use an one feature layer as Baseline.</li>
</ol>
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/ 	TransformToProfil_PolygonIntersection_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/ 	TransformToProfil_PolygonIntersection_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/ 	TransformToProfil_PolygonIntersection_Logo.png" style="max-width:100%;"></a></p>
#### Polygon - Baseline Intersections
````
Get the intersections from a polygon layer with the baseline and transform them to profile coordinates.
The intersection range can be represented through points or lines.
Select a line feature or use an one feature layer as Baseline.
````
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_Points_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_Points_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_Points_Logo.png" style="max-width:100%;"></a></p>
#### Points (incl. Bore Axis)
````
Transforms a point layer or selection to profile coordinates with considering of elevation.
If points has z values, they will used. 
If the the point z value are in a feature attribute
If the points have no realtionship to an elevation value, elevation is used from a Raster DEM.
Function only processes the points inside a buffer around the Baseline or if there is a selection, all selected points.
Extrapolation is not supported. Points have to be perpendicular to the baseline.
To create vertical lines (bore axis) use Dept Start and Dept End from freature attributes.
Select a line feature or use an one feature layer as Baseline.
If the baseline is a polylinestring, there could be blind spots.
````
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformGeomFromProfileToRealWorld_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformGeomFromProfileToRealWorld_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformGeomFromProfileToRealWorld_Logo.png" style="max-width:100%;"></a></p>
#### Reverse To Real World
````
Retransform point, line or polygon geometrys from profile coordinates back to real world geometry with Z values considering a baseline.
Select a line feature or use an one feature layer as Baseline.
````

### Vector Selection
#### Select duplicates
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/SelectDuplicates_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/SelectDuplicates_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/SelectDuplicates_Logo.png" style="max-width:100%;"></a></p>
````
Selects all duplicates in a field or based on a expression.
````

### Web

#### Download by Features
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/DowmloadByFile_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/DowmloadByFile_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/DowmloadByFile_Logo.png" style="max-width:100%;"></a></p>
````
Download files from a url based of a feature attribute.
````
#### Store WMS images by Features
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/StoreWMS_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/StoreWMS_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/StoreWMS_Logo.png" style="max-width:100%;"></a></p>
````
Download WMS images from a WMS server based of features bounding box.
World files will be created.
````

### Links
* [ThToolBox](https://plugins.qgis.org/plugins/ThToolBox/) - The PlugIn Website
* [github](https://github.com/Mi-Kbs-gis/ThToolBox) -GitHub Website

### Resources
<ul>
<li>Official QGIS plugins page: <a href="https://plugins.qgis.org/plugins/ThToolBox/" rel="nofollow">https://plugins.qgis.org/plugins/ThToolBox/</a></li>
<li>Documentation (De) <a href="https://github.com/Mi-Kbs-gis/ThToolBox/raw/master/help/ThToolBox_Doc_de.pdf" rel="nofollow">https://github.com/Mi-Kbs-gis/ThToolBox/raw/master/help/ThToolBox_Doc_de.pdf</a></li>
</ul>


### Authors

* **Michael Kürbs**  - [TLUBN](http://tlubn-thueringen.de)