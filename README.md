# TlugProcessing at master


## QGIS Processing Toolbox of TLUG
### Vector Selection Tools
#### Find duplicates
### To Profile Coordinates (Cross Section)
```
Geometrys would be transformed to a linear referencing by a baseline
```
#### Baseline
````
Transforms a single Line to profile coordinates with considering of elevation.
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
To create vertical lines (bore axis) use Dept Start und Dept End from freature attributes.
Select a line feature or use an one feature layer as Baseline.
````
#### Reverse To Real World
````
Retransform point, line or polygon geometry from profile coordinates back to real world considering a baseline.
Select a line feature or use an one feature layer as Baseline.
````
### Web

#### Download by Features
````
Download from a feature attribute
````
#### Rip WMS by Features
````
Download from a feature attribute
````

### Links
* [TlugProcessing](https://plugins.qgis.org/plugins/TlugProcessing/) -The PlugIn Website
* [github](https://github.com/Mi-Kbs-gis/TlugProcessing) -GitHub Website


### Authors

* **Michael Kürbs**  - [TLUG](https://www.thueringen.de/th8/tlug/)
