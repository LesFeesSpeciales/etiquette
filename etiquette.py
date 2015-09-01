import os, sys, subprocess

blender_bin = '/home/damien/blender-git/build_linux/bin/blender'

dirpath = os.path.dirname(__file__)
py_settings = os.path.join(dirpath, '_etiquette.py')

args = [blender_bin, '-b', '--factory-startup', '-P', py_settings, '--']
args.extend(sys.argv[1:])

subprocess.call(args)