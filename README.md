# TlugProcessing at master


## QGIS Processing Toolbox of TLUG
### 3D Tools

#### Attach raster values to line vertices
````
Process transform a LineString to LineStringZ geometry.
Two modes available
Mode "only vertices" sets Z-Values to given line vertices based on a (1 Band) raster data source.
Mode "fill by raster resolution" sets Z-Values to given line vertices and fill additional vertices based on the resolution of the raster layer.
````

### File Tools

#### Files To Table
````
Returns a table with entrys for each file in a directory. 
Include some file properties.
````

### To Profile Coordinates (Cross Section)
```
Geometrys would be transformed to a linear referencing by a baseline.
```
#### Baseline
````
Transforms a single Line to profile coordinates with considering of elevation.
On Raster NoDATA-Values, the profile elevation where set to 0.
Select a line feature or use an one feature layer as Baseline.
````
#### Line - Baseline Intersections
````
Get the intersections from a line layer with the baseline and transform them to profile coordinates.
Select a line feature or use an one feature layer as Baseline.
````
#### Polygon - Baseline Intersections
````
Get the intersections from a polygon layer with the baseline and transform them to profile coordinates.
The intersection range can be represented through points or lines.
Select a line feature or use an one feature layer as Baseline.
````
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
#### Reverse To Real World
````
Retransform point, line or polygon geometrys from profile coordinates back to real world geometry with Z values considering a baseline.
Select a line feature or use an one feature layer as Baseline.
````

### Vector Selection Tools
#### Select duplicates
````
Selects all duplicates in a field or based on a expression.
````

### Web

#### Download by Features
````
Download files from a url based of a feature attribute.
````
#### Store WMS images by Features
````
Download WMS images from a WMS server based of features bounding box.
World files will be created.
````

### Links
* [TlugProcessing](https://plugins.qgis.org/plugins/TlugProcessing/) -The PlugIn Website
* [github](https://github.com/Mi-Kbs-gis/TlugProcessing) -GitHub Website


### Authors

* **Michael Kürbs**  - [TLUG](https://www.thueringen.de/th8/tlug/)