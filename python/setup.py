#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext

# Read version from pyproject.toml
def read_version():
    try:
        import tomllib
        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)
        return data["project"]["version"]
    except ImportError:
        # fallback for Python < 3.11
        import configparser
        import re
        with open("pyproject.toml", "r") as f:
            content = f.read()
        match = re.search(r'version\s*=\s*"([^"]+)"', content)
        return match.group(1) if match else "0.9.0"

# Read the contents of README file
def read_readme():
    parent_dir = Path(__file__).parent.parent
    readme_path = parent_dir / "README.md"
    if readme_path.exists():
        return readme_path.read_text(encoding="utf-8")
    return "Python bindings for ldsCtrlEst"

class CMakeExtension(Extension):
    def __init__(self, name):
        Extension.__init__(self, name, sources=[])

class CMakeBuild(build_ext):
    def build_extension(self, ext):
        if isinstance(ext, CMakeExtension):
            self._build_cmake_extension(ext)
        else:
            super().build_extension(ext)

    def _build_cmake_extension(self, ext):
        # Get the absolute path to the build directory
        build_temp = Path(self.build_temp).resolve()
        build_temp.mkdir(parents=True, exist_ok=True)
        
        # Get the extension directory
        extdir = Path(self.get_ext_fullpath(ext.name)).parent.resolve()
        
        # Source directory (parent of python directory)
        source_dir = Path(__file__).parent.parent.resolve()
        
        # CMake configuration arguments
        cmake_args = [
            f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={extdir}/ldsctrlest",
            f"-DCMAKE_RUNTIME_OUTPUT_DIRECTORY={extdir}/ldsctrlest",
            f"-DCMAKE_ARCHIVE_OUTPUT_DIRECTORY={extdir}/ldsctrlest",
            f"-DPYTHON_EXECUTABLE={sys.executable}",
            f"-DPython_EXECUTABLE={sys.executable}",
            "-DLDSCTRLEST_BUILD_PYTHON=ON",
            f"-DCMAKE_BUILD_TYPE={'Debug' if self.debug else 'Release'}",
        ]

        # Check for vcpkg toolchain
        vcpkg_toolchain = source_dir / "vcpkg" / "scripts" / "buildsystems" / "vcpkg.cmake"
        if vcpkg_toolchain.exists():
            cmake_args.append(f"-DCMAKE_TOOLCHAIN_FILE={vcpkg_toolchain}")

        # Platform-specific arguments
        build_args = []
        if sys.platform.startswith("win"):
            cmake_args += ["-G", "Visual Studio 17 2022", "-A", "x64"]
            build_args += ["--config", "Debug" if self.debug else "Release"]
        else:
            cmake_args += ["-G", "Unix Makefiles"]
            build_args += ["--", f"-j{os.cpu_count() or 1}"]

        # Environment
        env = os.environ.copy()
        env["CXXFLAGS"] = f'{env.get("CXXFLAGS", "")} -DVERSION_INFO=\\"{self.distribution.get_version()}\\"'

        # Run CMake configure
        print(f"Running CMake configure in {build_temp}")
        print(f"Source directory: {source_dir}")
        print(f"CMake args: {cmake_args}")
        
        subprocess.check_call(
            ["cmake", str(source_dir)] + cmake_args,
            cwd=build_temp,
            env=env
        )
        
        # Run CMake build for Python modules only
        print("Building Python modules...")
        subprocess.check_call(
            ["cmake", "--build", ".", "--target", "python_modules"] + build_args,
            cwd=build_temp,
        )

        # Copy built modules to the right location
        self._copy_modules_to_package(build_temp, extdir)

    def _copy_modules_to_package(self, build_dir, extdir):
        """Copy the built Python modules to the package directory."""
        import shutil
        
        # Look for the built modules in the build directory
        python_build_dir = build_dir / "python" / "ldsctrlest"
        package_dir = extdir / "ldsctrlest"
        
        print(f"Looking for modules in: {python_build_dir}")
        print(f"Copying to: {package_dir}")
        
        if python_build_dir.exists():
            for module_file in python_build_dir.glob("*"):
                if module_file.is_file() and (
                    module_file.suffix in [".so", ".pyd", ".dll", ".dylib"] or
                    module_file.name in ["base.so", "gaussian.so", "poisson.so",
                                       "base.pyd", "gaussian.pyd", "poisson.pyd"]
                ):
                    dest = package_dir / module_file.name
                    print(f"Copying {module_file} to {dest}")
                    shutil.copy2(module_file, dest)

# Define extensions - these are placeholders since CMake builds them
extensions = [
    CMakeExtension("ldsctrlest._modules"),
]

setup(
    name="ldsctrlest",
    version=read_version(),
    description="Python bindings for ldsCtrlEst - estimation and control of linear dynamical systems",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Kyle Johnsen, Michael Bolus",
    url="https://github.com/CLOCTools/lds-ctrl-est",
    packages=["ldsctrlest"],
    package_data={
        "ldsctrlest": ["*.pyd", "*.lib", "*.pdb", "*.so", "*.dylib", "*.dll"]
    },
    include_package_data=True,
    ext_modules=extensions,
    cmdclass={"build_ext": CMakeBuild},
    zip_safe=False,
    python_requires=">=3.9",
    install_requires=[
        "numpy",
    ],
    extras_require={
        "test": ["pytest", "numpy"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research", 
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: C++",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
