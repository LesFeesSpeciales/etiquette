# ETIQUETTE

Etiquette is a command line tool used to stamp image sequences with whatever
needed information. Could be project/sequence/shot name, artist name, creation
date, version, frame, timecode, watermarks, logo, ...

Useful for chained actions, like after a lighting render is complete, or to send
videos to clients with important information.


## Usage
As of august 2015, the Blender binary has to be downloaded from the [Blender Buildbot](https://builder.blender.org/), or compiled from the latest git version, as it includes the Text Sequence used in the script.
Right now, the path to the **blender binary** has to be specified in the etiquette.py file, in the `blender_bin` variable.

The script is written in Python, and uses Blender for image marking and rendering. The script is command-line only at the moment. To get usage help, type:
```python etiquette.py --help```


## Template mode
A .json template file can be written to speed up the marking process, once a specification has been decided upon. In *template mode*, you have to call the script thus:
`python etiquette.py --template PATH/TO/TEMPLATE.json PATH/TO/IMAGE.ext [--options...]`
Type `--help` to get a list of options you can type. These options are specified in the template.json file, in the following form:
```
[
    {
        "field": "Plan",
        "value": "P01",
        "position": "BOTTOM-LEFT",
        "size": 15,
        "color": [
            0.0,
            0.0,
            0.0
        ],
        "inline": false
    }
]
```

You then have to pass arguments to the program according to the template, such as: `--plan P12`. **Alternatively**, you can use the `--default` option to use *all* fields defined in the template, with their default values.

## Metadata mode
The **Metadata mode** is similar to the Template Mode, but it uses a json string, passed in command line to the `--metadata` argument, to generate fields. For example, the following string will create an “A text” field and a “Frame” field:
```
--metadata '[{"field":"A text", "value":"Salut !", "color":[1.0,0.5,0.5]}, {"field":"Frame", "inline":false, "color":"#0137F0"}]'
```


## Special fields
Some fields have a special behaviour.
  * **Frame** and **Timecode** respectively print the frame and timecode, read from the file name.
  * **Date** prints the specified string, or defaults to today's date in DD/MM/YYYY format.


## Example template
```
{
    "settings":
    {"resolution":
        [1920,1080]
    },

    "metadata": 
    [
        {
            "position": "BOTTOM-LEFT",
            "value": "S001",
            "size": 15,
            "color": "#FF0000",
            "inline": false,
            "field": "S\u00e9quence"
        },
        {
            "position": "BOTTOM-LEFT",
            "value": "P01",
            "size": 15,
            "color": [
                0.0,
                0.0,
                1.0
            ],
            "inline": true,
            "field": "Plan"
        },
        {
            "position": "BOTTOM-LEFT",
            "value": null,
            "size": 15,
            "color": [
                0.0,
                0.0,
                1.0
            ],
            "inline": false,
            "field": "Frame"
        },
        {
            "position": "BOTTOM-LEFT",
            "value": null,
            "size": 15,
            "color": [
                0.0,
                0.0,
                0.0
            ],
            "inline": true,
            "field": "Timecode"
        },
        {
            "position": "TOP-LEFT",
            "value": "today",
            "size": 15,
            "color": "#00FF00",
            "inline": false,
            "field": "Date"
        }
    ]
}
```

This template generates the following image:

![](https://github.com/LesFeesSpeciales/tools/blob/master/stamp/example.png)

## License

Code shared by **Les Fées Spéciales** is, except where otherwise noted, licensed under [the CeCILL license](http://www.cecill.info/licences.fr.html) 2.1. All terms can be found [|here in French](http://www.cecill.info/licences/Licence_CeCILL_V2.1-fr.html) and [here in english](http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html)
