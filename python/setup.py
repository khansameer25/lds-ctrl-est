#!/usr/bin/env python3

import os
import re
import subprocess
import sys
from pathlib import Path
from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext

class CMakeExtension(Extension):
    def __init__(self, name):
        Extension.__init__(self, name, sources=[])

class CMakeBuild(build_ext):
    def apply_patches(self, source_dir):
        """Apply patches to CMake files for wheel building"""
        # Patch main CMakeLists.txt to skip HDF5 and Armadillo
        cmake_main = source_dir / "CMakeLists.txt"
        if cmake_main.exists():
            content = cmake_main.read_text()
            content = re.sub(r'include\(HDF5\)', '# include(HDF5) # Skipped for Python builds', content)
            content = re.sub(r'include\(Armadillo\)', '# include(Armadillo) # Skipped for Python builds', content)
            cmake_main.write_text(content)
        
        # Patch pybind11.cmake to remove Python3::Python from main library
        pybind11_cmake = source_dir / "cmake" / "Modules" / "pybind11.cmake"
        if pybind11_cmake.exists():
            content = pybind11_cmake.read_text()
            content = re.sub(
                r'list\(APPEND PROJECT_REQUIRED_LIBRARIES_ABSOLUTE_NAME carma::carma Python3::Python\)',
                'list(APPEND PROJECT_REQUIRED_LIBRARIES_ABSOLUTE_NAME carma::carma) # Python3::Python removed for wheel builds',
                content
            )
            pybind11_cmake.write_text(content)
    
    def build_extension(self, ext):
        if not isinstance(ext, CMakeExtension):
            return super().build_extension(ext)
            
        # Simple CMake build
        build_temp = Path(self.build_temp).resolve()
        build_temp.mkdir(parents=True, exist_ok=True)
        
        source_dir = Path(__file__).parent.parent.resolve()
        
        # Apply patches for wheel building
        self.apply_patches(source_dir)
        
        # Basic CMake args
        cmake_args = [
            f"-DCMAKE_BUILD_TYPE=Release",
            f"-DLDSCTRLEST_BUILD_PYTHON=ON",
            f"-DLDSCTRLEST_BUILD_FITTING=OFF",
            f"-DCMAKE_TOOLCHAIN_FILE=",
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
