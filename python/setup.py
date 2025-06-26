#!/usr/bin/env python3

import os
import shutil
import sys
from pathlib import Path
from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext

class CMakeExtension(Extension):
    def __init__(self, name):
        Extension.__init__(self, name, sources=[])

class CMakeBuild(build_ext):
    def build_extension(self, ext):
        if not isinstance(ext, CMakeExtension):
            return super().build_extension(ext)
        
        # The modules should already be built by CIBW_BEFORE_BUILD
        # Just copy them to the right location
        source_dir = Path(__file__).parent.parent.resolve()
        build_dir = source_dir / "build"
        
        # Find the built Python modules
        python_modules = list(build_dir.glob("**/python/ldsctrlest/*.so"))
        if not python_modules:
            python_modules = list(build_dir.glob("**/python/ldsctrlest/*.pyd"))
        
        if not python_modules:
            print("Warning: No Python modules found in build directory")
            print(f"Searched in: {build_dir}")
            # List contents for debugging
            if build_dir.exists():
                print("Build directory contents:")
                for item in build_dir.rglob("*"):
                    print(f"  {item}")
            return
        
        # Copy modules to package directory
        pkg_dir = Path(self.build_lib) / "ldsctrlest"
        pkg_dir.mkdir(parents=True, exist_ok=True)
        
        for module in python_modules:
            target = pkg_dir / module.name
            print(f"Copying {module} -> {target}")
            shutil.copy2(module, target)

setup(
    name="ldsctrlest",
    version="0.9.0",
    packages=["ldsctrlest"],
    ext_modules=[CMakeExtension("ldsctrlest._modules")],
    cmdclass={"build_ext": CMakeBuild},
    install_requires=["numpy"],
    python_requires=">=3.9",
)
