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
</ol>

### File Tools

#### Files To Table
<ol>
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/Files2Table_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/Files2Table_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/Files2Table_Logo.png" style="max-width:100%;"></a></p>
<p>Returns a table with entrys for each file in a directory.</p>
<p>Include some file properties.</p>
</ol>

### To Profile Coordinates (Cross Section)
<ol>
<p>Geometrys would be transformed to a linear referencing by a baseline.</p>

<h2>Raster Gradient</h2>
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_Gradient_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_Gradient_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_Gradient_Logo.png" style="max-width:100%;"></a></p>
<ol>
<p>Transforms a single Line to profile coordinates with considering of elevation.</p>
<p>On Raster NoDATA-Values, the profile elevation where set to 0.</p>
<p>Select a line feature or use an one feature layer as Baseline.</p>
</ol>
<h3>Line - Baseline Intersections</h3>
<ol>
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_LineIntersection_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_LineIntersection_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_LineIntersection_Logo.png" style="max-width:100%;"></a></p>
<p>Get the intersections from a line layer with the baseline and transform them to profile coordinates.</p>
<p>Select a line feature or use an one feature layer as Baseline.</p>
</ol>
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/ 	TransformToProfil_PolygonIntersection_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/ 	TransformToProfil_PolygonIntersection_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/ 	TransformToProfil_PolygonIntersection_Logo.png" style="max-width:100%;"></a></p>
#### Polygon - Baseline Intersections
<ol>
<p>Get the intersections from a polygon layer with the baseline and transform them to profile coordinates.</p>
<p>The intersection range can be represented through points or lines.</p>
<p>Select a line feature or use an one feature layer as Baseline.</p>
</ol>
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_Points_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_Points_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_Points_Logo.png" style="max-width:100%;"></a></p>
#### Points (incl. Bore Axis)
<ol>
<p>Transforms a point layer or selection to profile coordinates with considering of elevation.</p>
<p>If points has z values, they will used. </p>
<p>If the the point z value are in a feature attribute</p>
<p>If the points have no realtionship to an elevation value, elevation is used from a Raster DEM.</p>
<p>Function only processes the points inside a buffer around the Baseline or if there is a selection, all selected points.</p>
<p>Extrapolation is not supported. Points have to be perpendicular to the baseline.</p>
<p>To create vertical lines (bore axis) use Dept Start and Dept End from freature attributes.</p>
<p>Select a line feature or use an one feature layer as Baseline.</p>
<p>If the baseline is a polylinestring, there could be blind spots.</p>
</ol>
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformGeomFromProfileToRealWorld_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformGeomFromProfileToRealWorld_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformGeomFromProfileToRealWorld_Logo.png" style="max-width:100%;"></a></p>
#### Reverse To Real World
<ol>
<p>Retransform point, line or polygon geometrys from profile coordinates back to real world geometry with Z values considering a baseline.</p>
<p>Select a line feature or use an one feature layer as Baseline.</p>
</ol>
</ol>
### Vector Selection
#### Select duplicates
<ol>
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/SelectDuplicates_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/SelectDuplicates_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/SelectDuplicates_Logo.png" style="max-width:100%;"></a></p>
<p>Selects all duplicates in a field or based on a expression.</p>
</ol>

### Web

#### Download by Features
<ol>
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/DowmloadByFile_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/DowmloadByFile_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/DowmloadByFile_Logo.png" style="max-width:100%;"></a></p>
<p>Download files from a url based of a feature attribute.</p>
</ol>
#### Store WMS images by Features
<ol>
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/StoreWMS_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/StoreWMS_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/StoreWMS_Logo.png" style="max-width:100%;"></a></p>
<p>Download WMS images from a WMS server based of features bounding box.</p>
<p>World files will be created.</p>
</ol>

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