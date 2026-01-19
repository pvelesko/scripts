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
parser.add_argument('--lua', '-l', action='store_true', help='generate Lua module instead of TCL')
args = parser.parse_args()

if not args.module_name:
    if "/install/" not in args.install_dir:
        print("Error: install_dir must contain '/install/' to auto-generate module_name.")
        sys.exit(1)
    _, module_name = args.install_dir.split("/install/", 1)
    args.module_name = module_name
else:
    module_name = args.module_name
    
package_name = module_name.split('/')[0]
package_name_upper = package_name.upper()

# drop trailing slash if present from install_dir
if args.install_dir[-1] == '/':
    args.install_dir = args.install_dir[:-1]

module = []

if args.lua:
    # Lua format
    module.append("-- -*- lua -*-")
    module.append(f'local install_dir = "{args.install_dir}"')
    module.append("")
    
    if args.prereq:
        for prereq in args.prereq:
            module.append(f'depends_on("{prereq}")')
        module.append("")
    
    if args.extra:
        for extra in args.extra:
            var, val = extra.split('=')
            if val == "install_dir" or val == "$install_dir":
                module.append(f'setenv("{var}", install_dir)')
            else:
                module.append(f'setenv("{var}", "{val}")')
    
    module.append(f'setenv("{package_name}_PATH", install_dir)')
    module.append(f'setenv("{package_name}_ROOT", install_dir)')
    module.append(f'setenv("{package_name}_DIR", install_dir)')
    module.append(f'setenv("{package_name_upper}_PATH", install_dir)')
    module.append(f'setenv("{package_name_upper}_ROOT", install_dir)')
    module.append(f'setenv("{package_name_upper}_DIR", install_dir)')
    
    # Check for CMake module subdirectory
    module_subdir = os.path.join(args.install_dir, package_name)
    if os.path.exists(module_subdir) and os.path.isdir(module_subdir):
        has_cmake_files = any(f.endswith('.cmake') for f in os.listdir(module_subdir) if os.path.isfile(os.path.join(module_subdir, f)))
        if has_cmake_files:
            module_var = f"{package_name_upper.replace('-', '_')}_MODULE_PATH"
            module.append(f'setenv("{module_var}", install_dir .. "/{package_name}")')
    
    module.append("")
    module.append('prepend_path("PATH", install_dir .. "/bin")')
    module.append('prepend_path("LD_LIBRARY_PATH", install_dir .. "/lib")')
    module.append('prepend_path("LD_LIBRARY_PATH", install_dir .. "/lib64")')
    if sys.platform == "darwin":
        # On macOS, use DYLD_FALLBACK_LIBRARY_PATH instead of DYLD_LIBRARY_PATH.
        # DYLD_LIBRARY_PATH takes precedence over @rpath, which breaks libraries
        # that rely on @rpath to find their dependencies (e.g. PoCL finding LLVM).
        # DYLD_FALLBACK_LIBRARY_PATH is checked after @rpath, matching the behavior
        # of LD_LIBRARY_PATH on Linux where rpath takes precedence.
        module.append('prepend_path("DYLD_FALLBACK_LIBRARY_PATH", install_dir .. "/lib")')
        module.append('prepend_path("DYLD_FALLBACK_LIBRARY_PATH", install_dir .. "/lib64")')
    module.append('prepend_path("LIBRARY_PATH", install_dir .. "/lib")')
    module.append('prepend_path("LIBRARY_PATH", install_dir .. "/lib64")')
    module.append('prepend_path("CPATH", install_dir .. "/include")')
    module.append('prepend_path("PKG_CONFIG_PATH", install_dir .. "/lib/pkgconfig")')
    module.append('prepend_path("CMAKE_PREFIX_PATH", install_dir)')
else:
    # TCL format
    module.append("#%Module")
    
    if args.prereq:
        for prereq in args.prereq:
            module.append(f"prereq {prereq}")
    
    module.append("")
    module.append(f"set install_dir {args.install_dir}")
    
    if args.extra:
        for extra in args.extra:
            var, val = extra.split('=')
            if val == "install_dir":
                val = "$install_dir"
            module.append(f'pushenv {var} "{val}"')
    
    module.append(f"pushenv {package_name}_PATH $install_dir")
    module.append(f"pushenv {package_name}_ROOT $install_dir")
    module.append(f"pushenv {package_name}_DIR $install_dir")
    module.append(f"pushenv {package_name_upper}_PATH $install_dir")
    module.append(f"pushenv {package_name_upper}_ROOT $install_dir")
    module.append(f"pushenv {package_name_upper}_DIR $install_dir")
    
    # Check for CMake module subdirectory
    module_subdir = os.path.join(args.install_dir, package_name)
    if os.path.exists(module_subdir) and os.path.isdir(module_subdir):
        has_cmake_files = any(f.endswith('.cmake') for f in os.listdir(module_subdir) if os.path.isfile(os.path.join(module_subdir, f)))
        if has_cmake_files:
            module_var = f"{package_name_upper.replace('-', '_')}_MODULE_PATH"
            module.append(f"pushenv {module_var} $install_dir/{package_name}")
    
    module.append("")
    module.append("prepend-path PATH $install_dir/bin")
    if sys.platform == "darwin":
        # On macOS, use DYLD_FALLBACK_LIBRARY_PATH instead of DYLD_LIBRARY_PATH.
        # DYLD_LIBRARY_PATH takes precedence over @rpath, which breaks libraries
        # that rely on @rpath to find their dependencies (e.g. PoCL finding LLVM).
        # DYLD_FALLBACK_LIBRARY_PATH is checked after @rpath, matching the behavior
        # of LD_LIBRARY_PATH on Linux where rpath takes precedence.
        module.append("prepend-path DYLD_FALLBACK_LIBRARY_PATH $install_dir/lib")
        module.append("prepend-path DYLD_FALLBACK_LIBRARY_PATH $install_dir/lib64")
    else:
        module.append("prepend-path LD_LIBRARY_PATH $install_dir/lib")
        module.append("prepend-path LD_LIBRARY_PATH $install_dir/lib64")
    module.append("prepend-path LIBRARY_PATH $install_dir/lib")
    module.append("prepend-path LIBRARY_PATH $install_dir/lib64")
    module.append("prepend-path CPATH $install_dir/include")
    module.append("prepend-path PKG_CONFIG_PATH $install_dir/lib/pkgconfig")
    module.append("prepend-path CMAKE_PREFIX_PATH $install_dir/lib/cmake")

# Get full file path with .lua extension if needed
file_ext = ".lua" if args.lua else ""
full_path = f"{args.modulefiles}/{module_name}{file_ext}"
if full_path[-1] == '/':
    full_path = full_path[:-1]

print(f"Generating modulefile {full_path}")
print(f"The module can be loaded by running: module load {module_name}")

# Print the details and contents of the modulefile before writing to disk
print("\nModulefile contents:")
print("-" * 40)
for line in module:
    print(line)
print("-" * 40)

# Get user confirmation before writing to disk
input("Press Enter to confirm and write modulefile to disk...")

# Get the directory path
dir_path = os.path.dirname(full_path)

# Check if the file already exists
if os.path.exists(full_path):
    print(f"\nmodulefile already exists at {full_path}")
    sys.exit(0)

if os.path.isfile(dir_path):
    print(f"\nmodulefile already exists at {dir_path}")
    sys.exit(0)

# Make the dirs if they don't exist
os.makedirs(dir_path, exist_ok=True)

# Write the module file to disk
with open(full_path, 'w') as f:
    for line in module:
        f.write(line + "\n")

print(f"Modulefile written to: {full_path}")
