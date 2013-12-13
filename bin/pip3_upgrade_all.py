#!/usr/bin/env python3

"""
Script for upgrading all modules using pip command-line tool.
Source: http://stackoverflow.com/a/5839291/548696
"""

import pip
from subprocess import call

for dist in pip.get_installed_distributions():
    call("pip3 install --upgrade " + dist.project_name, shell=True)
