#!/usr/bin/env python3
import sys
import os
import argparse

home = os.environ['HOME']
parser = argparse.ArgumentParser(
                    prog = 'Generate a modulefile for an intalled package',
                    description = 'Sets up PATH and LD_LIBRARY_PATH along with optional env vars',
                    epilog = '')
parser.add_argument('install_dir', help='path to the install directory')
parser.add_argument('module_name', help='full name of the module. Ex: cuda/versions/10.1.234')
parser.add_argument('--modulefiles', '-m', help='path to the modulefiles directory', default='{home}/local/modulefiles'.format(home=home))
parser.add_argument('--extra', '-e', action='append', help='additional env var to export. Install dir can be accessed as install_dir. Ex: -e "HIP_DIR=install_dir"')
parser.add_argument('--prereq', '-p', action='append', help='prereq modules. Ex: -p "gcc/8.3.0"')
args = parser.parse_args()
print("Generating modulefile {module_name} in {modulefiles}".format(module_name=args.module_name, modulefiles=args.modulefiles))
print("The module can be loaded by running: module load {module_name}".format(module_name=args.module_name))

module = []

module.append("#%Module")

if args.prereq:
    for prereq in args.prereq:
        module.append("prereq {prereq}".format(prereq=prereq))

module.append("")

module.append("set install_dir {install_dir}".format(install_dir=args.install_dir))

if args.extra:
    for extra in args.extra:
        var, val = extra.split('=')
        if val == "install_dir":
            val = "$install_dir"
        module.append("setenv {var} \"{val}\"".format(var=var, val=val))

module.append("")
module.append("prepend-path PATH {install_dir}/bin".format(install_dir=args.install_dir))
module.append("prepend-path LD_LIBRARY_PATH {install_dir}/lib".format(install_dir=args.install_dir))
module.append("prepend-path LD_LIBRARY_PATH {install_dir}/lib64".format(install_dir=args.install_dir))
module.append("prepend-path LIBRARY_PATH {install_dir}/lib".format(install_dir=args.install_dir))
module.append("prepend-path LIBRARY_PATH {install_dir}/lib64".format(install_dir=args.install_dir))
module.append("prepend-path CPATH {install_dir}/include".format(install_dir=args.install_dir))

# Get full file path
full_path = "{modulefiles}/{module_name}".format(modulefiles=args.modulefiles, module_name=args.module_name)

# Get the directory path
dir_path = os.path.dirname(full_path)

# Make the dirs if they don't exist
os.makedirs(dir_path, exist_ok=True)

with open(full_path, 'w') as f:
    for line in module:
        f.write(line + "\n")
