#!/usr/bin/env python3

import os
import subprocess
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
            
        # Simple CMake build
        build_temp = Path(self.build_temp).resolve()
        build_temp.mkdir(parents=True, exist_ok=True)
        
        source_dir = Path(__file__).parent.parent.resolve()
        
        # Basic CMake args
        cmake_args = [
            f"-DCMAKE_BUILD_TYPE=Release",
            f"-DLDSCTRLEST_BUILD_PYTHON=ON",
            f"-DPYTHON_EXECUTABLE={sys.executable}",
        ]
        
        # Run CMake
        subprocess.check_call(["cmake", str(source_dir)] + cmake_args, cwd=build_temp)
        subprocess.check_call(["cmake", "--build", ".", "--target", "python_modules"], cwd=build_temp)

setup(
    name="ldsctrlest",
    version="0.9.0",
    packages=["ldsctrlest"],
    ext_modules=[CMakeExtension("ldsctrlest._modules")],
    cmdclass={"build_ext": CMakeBuild},
    install_requires=["numpy"],
    python_requires=">=3.9",
)
