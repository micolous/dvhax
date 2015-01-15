# dvhax #

Tool for inspecting the structure of DV files.


## Command line interface ##

### Get aspect ratio of a DV file ###

```
$ python dvhax.py somefile.dv ar
r4_3
````

Valid return values:

* `r4_3`: 4:3
* `r16_9_letterbox`: 16:9 video in a 4:3 letterbox
* `r16_9_fullframe`: 16:9 video, full frame
* `unknown`: Nobody knows!


### Get lots of info about a DV file ###

```
$ python dvhax.py somefile.dv pretty
... lots of metadata
```

Prints lots of metadata about the first segment of the DV file.

## Notes ##

* http://dvswitch.alioth.debian.org/wiki/DV_format/

