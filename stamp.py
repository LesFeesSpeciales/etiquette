from __future__ import print_function

import os, sys, subprocess

blender_bin = '/home/damien/blender-git/build_linux/bin/blender'

dirpath = os.path.dirname(__file__)
py_settings = os.path.join(dirpath, 'stamp_settings.py')

args = [blender_bin, '-b', '--factory-startup', '-P', py_settings, '--']
args.extend(sys.argv[1:])

# print('    ARGS', args)
# print('    FILE', os.path.abspath(__file__))

subprocess.call(args)
# -b --p [..]/stamp.py -- imagepath1 imagepath2 -frame -date -etcetera