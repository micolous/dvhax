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

### Patch the aspect ratio in a DV file ###

```
$ python arpatch.py broken.dv --ar r16_9_fullframe
Patching AR to r16_9_fullframe
Patched AR at 455 bytes (0x1C7)
```

Valid aspect ratios shows above.  Patches the file in-place.

You can also have it patch ALL of the file, but this is dangerous.

```
$ python arpatch.py broken.dv --ar r16_9_fullframe --all
Patching AR to r16_9_fullframe
Patched AR at 455 bytes (0x1C7)
.... many more ....
```

Technically a DV file can have it's aspect ratio change mid-stream.  However, in reality, many video players only read the FIRST instance of this, and will continue along with the rest of the stream.

## Notes ##

* http://dvswitch.alioth.debian.org/wiki/DV_format/

