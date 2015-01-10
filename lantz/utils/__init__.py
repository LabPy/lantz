# -*- coding: utf-8 -*-
"""
    lantz.utils
    ~~~~~~~~~~~

    A package with utility modules.

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import os

# Indicates if the documentation is being built in the current process.
# :type: bool
is_building_docs = os.environ.get('LANTZ_BUILDING_DOCS', 'False') == 'True'
