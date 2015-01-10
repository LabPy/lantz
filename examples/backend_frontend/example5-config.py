# -*- coding: utf-8 -*-
"""
    lantz.action
    ~~~~~~~~~~~~

    This example shows how to use a more complex app, loading the configuration
    from an external file and


    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

# From lantz, you import a helper function.
from lantz.ui.app import start_gui_app


from myapps import AmplitudeScannerShutter, AmplitudeScannerShutterUi

# To instantiated BigApp in this example, the configuration is loaded from a yaml file
# For each instrument in the yaml file, the corresponding one in BigApp is found (matched by name).
# an assigned to a new instance of the driver created using the corresponding class, args and kwargs.

# Then variables are checked to see if they are an instance of Backend (in this case scanner).
# In that case, "sub qapp" is instantiated. When BigApp notice that `osci` and `fungen` are
# also present in the small qapp, it will assign the corresponding drivers
# (a way should be provided to use subapps with different naming)

app = AmplitudeScannerShutter.config_from_file('lab_config.yaml')

# calling show, displays the user interface and blocks the execution
# under the hood it creates a QtApp and start it.

start_gui_app(app, AmplitudeScannerShutterUi)
