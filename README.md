# ThToolBox at master


## QGIS Processing Toolbox of Thüringer Landesamt für Umwelt, Bergbau und Naturschutz (TLUBN)
<h2>2D -> 3D</h2>
<ol>
<h3>Attach raster values to line vertices</h3>
<ol>
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/AttachZvalOnLine_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/AttachZvalOnLine_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/AttachZvalOnLine_Logo.png" style="max-width:100%;"></a></p>
<p>Process transform a LineString to LineStringZ geometry.</p>
<p>Two modes available</p>
<p>Mode "only vertices" sets Z-Values to given line vertices based on a (1 Band) raster data source.</p>
<p>Mode "fill by raster resolution" sets Z-Values to given line vertices and fill additional vertices based on the resolution of the raster layer.</p>
</ol>
</ol>
<h2>File Tools</h2>
<ol>
<h3>Files To Table</h3>
<ol>
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/Files2Table_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/Files2Table_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/Files2Table_Logo.png" style="max-width:100%;"></a></p>
<p>Returns a table with entrys for each file in a directory.</p>
<p>Include some file properties.</p>
</ol>
<h3>File Transfer By Table</h3>
<ol>
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/FileTransferByTable_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/FileTransferByTable_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/FileTransferByTable_Logo.png" style="max-width:100%;"></a></p>
<p>Algorithm perfomrs a file transfer, which is defined via source and target filelinks a table or Layer</p>
<p>There is also a functionality for overwriting and backup of existing files.</p>
</ol>
</ol>
<h2>To Profile Coordinates (Cross Section Geometrys)</h2>
<ol>
<p>Geometrys would be transformed to a linear referencing by a baseline.</p>

<h3>Raster Gradient</h3>
<ol>
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_Gradient_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_Gradient_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_Gradient_Logo.png" style="max-width:100%;"></a></p>
<p>Transforms a single Line to profile coordinates with considering of elevation.</p>
<p>Raster NoDATA, zero or negative values can be excluded in the result</p>
<p>Kinked base lines are permitted and will be fully processed.</p>
<p>Select a line feature or use an one feature layer as Baseline.</p>
</ol>
<h3>Line - Baseline Intersections</h3>
<ol>
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_LineIntersection_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_LineIntersection_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_LineIntersection_Logo.png" style="max-width:100%;"></a></p>
<p>Get the intersections from a line layer with the baseline and transform them to profile coordinates.</p>
<p>Kinked base lines are permitted and will be fully processed.</p>
<p>Select a line feature or use an one feature layer as Baseline.</p>
</ol>
<h3>Plane - Baseline Intersections (directed points)</h3>
<ol>
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_PlaneIntersection_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_PlaneIntersection_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_PlaneIntersection_Logo.png" style="max-width:100%;"></a></p>
<p>This function calculates the intersection lines of a series of planes with the vertical cross-section plane. A point plane with horizontal and vertical angles is required for the input planes.</p>
<p>The horizonal direction means the directional angle from north, measures clockwise in degrees. (north=0°; east=90°; west=270°)</p>
<p>The angle of depression is measured between horizontal an the direction of fall in degrees. (horizontal=0°; nadir=90°)</p>
<p>Kinked base lines are permitted and will be fully processed.</p>
<p>Select a line feature or use an one feature layer as Baseline.</p>
</ol>
<h3>Polygon - Baseline Intersections</h3>
<ol>
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_PolygonIntersection_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_PolygonIntersection_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_PolygonIntersection_Logo.png" style="max-width:100%;"></a></p>
<p>Get the intersections from a polygon layer with the baseline and transform them to profile coordinates.</p>
<p>The intersection range can be represented through points or lines.</p>
<p>Kinked base lines are permitted and will be fully processed.</p>
<p>Select a line feature or use an one feature layer as Baseline.</p>
</ol>
<h3>Points (incl. Bore Axis)</h3>
<ol>
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_Points_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_Points_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformToProfil_Points_Logo.png" style="max-width:100%;"></a></p>
<p>Transforms a point layer or selection to profile coordinates with considering of elevation.</p>
<p>If points has z values, they will used. </p>
<p>If the the point z value are in a feature attribute</p>
<p>If the points have no realtionship to an elevation value, elevation is used from a Raster DEM.</p>
<p>Function only processes the points inside a buffer around the Baseline or if there is a selection, all selected points.</p>
<p>Extrapolation is not supported. Points have to be perpendicular to the baseline.</p>
<p>To create vertical lines (bore axis) use Dept Start and Dept End from freature attributes.</p>
<p>Select a line feature or use an one feature layer as Baseline.</p>
<p>Kinked base lines are permitted and will be fully processed. But in this case, points located in the blind spots of a kink point cannot be processed successfully.</p>
</ol>
<h3>Reverse To Real World</h3>
<ol>
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformGeomFromProfileToRealWorld_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformGeomFromProfileToRealWorld_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/TransformGeomFromProfileToRealWorld_Logo.png" style="max-width:100%;"></a></p>
<p>Retransform point, line or polygon geometrys from profile coordinates back to real world geometry with Z values considering a baseline.</p>
<p>Kinked base lines are permitted and will be fully processed.</p>
<p>The processing of the offset is constant for an entire geometry object.</p>
<p>Select a line feature or use an one feature layer as Baseline.</p>
</ol>
</ol>
<h2>Vector Selection</h2>
<ol>
<h3>Select duplicates</h3>
<ol>
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/SelectDuplicates_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/SelectDuplicates_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/SelectDuplicates_Logo.png" style="max-width:100%;"></a></p>
<p>Selects all duplicates in a field or based on a expression.</p>
</ol>
</ol>
<h2>Web</h2>
<ol>
<h3>Download by Features</h3>
<ol>
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/DowmloadByFile_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/DowmloadByFile_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/DowmloadByFile_Logo.png" style="max-width:100%;"></a></p>
<p>Download files from a url based of a feature attribute.</p>
</ol>
<h3>Store WMS images by Features</h3>
<ol>
<p><a target="_blank" rel="noopener noreferrer" href="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/StoreWMS_Logo.png"><img src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/StoreWMS_Logo.png" alt="" data-canonical-src="https://github.com/Mi-Kbs-gis/ThToolBox/blob/master/icons/StoreWMS_Logo.png" style="max-width:100%;"></a></p>
<p>Download WMS images from a WMS server based of features bounding box.</p>
<p>World files will be created.</p>
</ol>
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