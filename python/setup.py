from setuptools import setup, find_packages

setup(
    name="ldsctrlest",
    version="0.9.0",
    description="Python bindings for ldsCtrlEst",
    author="Kyle Johnsen, Michael Bolus",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "ldsctrlest": ["*.so", "*.pyd", "*.dll", "*.dylib", "*.lib", "*.pdb"],
    },
    python_requires=">=3.6",
    license="Apache-2.0",
)
