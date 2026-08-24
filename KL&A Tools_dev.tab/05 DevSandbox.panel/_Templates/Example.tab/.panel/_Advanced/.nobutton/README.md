## No-Button Bundle

```
extension: .nobutton
```

No-Button bundles are just like Push Button bundles except that they will never show up inside Revit UI and thus don’t need any icons. The only way to run these commands is through pyRevit ***Search*** tool. These commands are meant for more advanced commands that not every user needs, and so they remain fairly hidden.

Open the pyRevit ***Search*** and run `testcmdargs -h` and see what happens.

![](https://s3-us-west-2.amazonaws.com/secure.notion-static.com/0e480dd5-0b5f-4e24-b408-c8505d1d029d/2019-08-30_10_42_19-Autodesk_Revit_2019.2_-_Project1.rvt_-_Floor_Plan__Level_1.png)

![](https://s3-us-west-2.amazonaws.com/secure.notion-static.com/960202c1-7efb-417b-9bd4-39a6a3e378ab/2019-08-30_10_42_28-testcmdargs.png)

This is the source for this test command that uses the `docopt` module to process the input arguments

"""Test docopt argument processing.

Usage:
    testdocopt (-h | --help)
    testdocopt (-V | --version)
    testdocopt -e <encod> <src_file>

Options:
    -h, --help                          Show this help
    -V, --version                       Show command version
    -e <encod>, --encode <encod>        File encoding [default: utf-8]
"""

import sys
import docopt

args = docopt.docopt(__doc__,
                     version='testdocopt {}'.format('v0.1'),
                     help=True)
