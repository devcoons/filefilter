#########################################################################################
#                                                                                       #
# MIT License                                                                           #
#                                                                                       #
# Copyright (c) 2025 Ioannis D. (devcoons)                                              #
#                                                                                       #
# Permission is hereby granted, free of charge, to any person obtaining a copy          #
# of this software and associated documentation files (the "Software"), to deal         #
# in the Software without restriction, including without limitation the rights          #
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell             #
# copies of the Software, and to permit persons to whom the Software is                 #
# furnished to do so, subject to the following conditions:                              #
#                                                                                       #
# The above copyright notice and this permission notice shall be included in all        #
# copies or substantial portions of the Software.                                       #
#                                                                                       #
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR            #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,              #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE           #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER                #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,         #
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE         #
# SOFTWARE.                                                                             #
#                                                                                       #
#########################################################################################

#########################################################################################
# IMPORTS                                                                               #
#########################################################################################

import os
from .utilities import *

#########################################################################################
#########################################################################################

class Ruleset:
    """Resolved root + parsed filters ready for matching."""
    def __init__(self, data: dict, resolve_base: str = ''):
        raw_root_original = str(data["root_dir"]).strip()
        if os.path.isabs(raw_root_original):
            root = raw_root_original
        else:
            if resolve_base in ("", "cwd"):
                base_dir = os.getcwd()
            elif resolve_base == "script":
                base_dir = os.path.dirname(os.path.abspath(__file__))
            else:
                base_dir = resolve_base
            root = os.path.join(base_dir, raw_root_original)
        self.root_dir = os.path.normpath(root)

        inc = data['filters']['include']
        exc = data['filters']['exclude']

        self.inc_dirs_root, self.inc_dirs_one, self.inc_dirs_any = parse_dir_patterns(inc.get('dirs', []))
        self.exc_dirs_root, self.exc_dirs_one, self.exc_dirs_any = parse_dir_patterns(exc.get('dirs', []))

        self.include_files = parse_file_patterns(inc.get('files', []))
        self.exclude_files = parse_file_patterns(exc.get('files', []))

        self.inc_exts = parse_extensions(inc.get('extensions', []))
        self.exc_exts = parse_extensions(exc.get('extensions', []))

#########################################################################################
#########################################################################################