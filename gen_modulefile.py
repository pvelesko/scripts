#!/usr/bin/env python3
import sys
import os
import argparse

home = os.environ['HOME']
parser = argparse.ArgumentParser(
                    prog = 'Generate a modulefile for an installed package',
                    description = 'Sets up PATH and LD_LIBRARY_PATH along with optional env vars',
                    epilog = '')
parser.add_argument('--modulefiles', default=f"{home}/modulefiles", help='path to the modulefiles directory (default: $HOME/modulefiles)')
parser.add_argument('install_dir', help='path to the install directory')
parser.add_argument('module_name', nargs='?', help='full name of the module. Ex: cuda/versions/10.1.234')
parser.add_argument('--extra', '-e', action='append', help='additional env var to export. Install dir can be accessed as install_dir. Ex: -e "HIP_DIR=$install_dir"')
parser.add_argument('--prereq', '-p', action='append', help='prereq modules. Ex: -p "gcc/8.3.0"')
args = parser.parse_args()

if not args.module_name:
    if "/install/" not in args.install_dir:
        print("Error: install_dir must contain '/install/' to auto-generate module_name.")
        sys.exit(1)
    install_base, module_name = args.install_dir.split("/install/", 1)
    args.install_dir = install_base + "/install"
    args.module_name = module_name
else:
    module_name = args.module_name

print("Generating modulefile {module_name} in {modulefiles}".format(module_name=module_name, modulefiles=args.modulefiles))
print("The module can be loaded by running: module load {module_name}".format(module_name=module_name))

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
module.append("prepend-path PATH $install_dir/bin")
module.append("prepend-path LD_LIBRARY_PATH $install_dir/lib")
module.append("prepend-path LD_LIBRARY_PATH $install_dir/lib64")
module.append("prepend-path LIBRARY_PATH $install_dir/lib")
module.append("prepend-path LIBRARY_PATH $install_dir/lib64")
module.append("prepend-path CPATH $install_dir/include")

# Print the details and contents of the modulefile before writing to disk
print("\nModulefile contents:")
print("-" * 40)
for line in module:
    print(line)
print("-" * 40)

# Get user confirmation before writing to disk
input("Press Enter to confirm and write modulefile to disk...")

# Get full file path
full_path = "{modulefiles}/{module_name}".format(modulefiles=args.modulefiles, module_name=module_name)

# Get the directory path
dir_path = os.path.dirname(full_path)

# Make the dirs if they don't exist
os.makedirs(dir_path, exist_ok=True)

# Write the module file to disk
with open(full_path, 'w') as f:
    for line in module:
        f.write(line + "\n")

print("Modulefile written to: {}".format(full_path))
