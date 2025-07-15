cmake_minimum_required(VERSION 3.16)
project(ldsctrlest VERSION 0.9.0 LANGUAGES CXX C)

# Set up paths relative to main project
set(MAIN_PROJECT_DIR ${CMAKE_SOURCE_DIR}/..)
set(CMAKE_MODULE_PATH ${MAIN_PROJECT_DIR}/cmake/Modules ${CMAKE_MODULE_PATH})

# If vcpkg toolchain is available, use it
if(DEFINED CMAKE_TOOLCHAIN_FILE)
    message(STATUS "Using vcpkg toolchain: ${CMAKE_TOOLCHAIN_FILE}")
endif()

# Find Python3 with NumPy (required for carma)
# Handle manylinux container case differently
if(DEFINED ENV{CIBW_LINUX})
    message(STATUS "Detected manylinux build environment")
    # In manylinux containers, set Python variables manually from environment
    if(DEFINED ENV{Python3_EXECUTABLE})
        set(Python3_EXECUTABLE $ENV{Python3_EXECUTABLE} CACHE FILEPATH "Python executable")
        message(STATUS "Using Python executable: ${Python3_EXECUTABLE}")
    endif()
    if(DEFINED ENV{Python3_INCLUDE_DIR})
        set(Python3_INCLUDE_DIRS $ENV{Python3_INCLUDE_DIR} CACHE PATH "Python include directory")
        message(STATUS "Using Python include dir: ${Python3_INCLUDE_DIRS}")
    endif()
    if(DEFINED ENV{Python3_LIBRARY})
        set(Python3_LIBRARIES $ENV{Python3_LIBRARY} CACHE FILEPATH "Python library")
        message(STATUS "Using Python library: ${Python3_LIBRARIES}")
    endif()
    # Find NumPy separately
    find_package(Python3 COMPONENTS Interpreter NumPy REQUIRED)
else()
    # Normal case: find full development components
    find_package(Python3 COMPONENTS Interpreter Development NumPy REQUIRED)
endif()

# Find pybind11
find_package(pybind11 REQUIRED)

# Add carma as subdirectory (header-only library)
add_subdirectory(carma)

# Include directories from main project
include_directories(${MAIN_PROJECT_DIR}/include)

# Add the source files to build the main library
file(GLOB_RECURSE LIB_SOURCES 
    ${MAIN_PROJECT_DIR}/src/*.cpp
    ${MAIN_PROJECT_DIR}/src-fit/*.cpp
)

# Create the main library
add_library(${CMAKE_PROJECT_NAME} SHARED ${LIB_SOURCES})

# Set C++ standard conditionally - C++17 for Linux manylinux, C++14 for macOS
if(CMAKE_SYSTEM_NAME STREQUAL "Linux" AND DEFINED ENV{CIBW_LINUX})
    set_property(TARGET ${CMAKE_PROJECT_NAME} PROPERTY CXX_STANDARD 17)
else()
    set_property(TARGET ${CMAKE_PROJECT_NAME} PROPERTY CXX_STANDARD 14)
endif()
set_property(TARGET ${CMAKE_PROJECT_NAME} PROPERTY CXX_STANDARD_REQUIRED ON)

# Set shared library properties for better auditwheel compatibility
set_target_properties(${CMAKE_PROJECT_NAME} PROPERTIES
    VERSION ${PROJECT_VERSION}
    SOVERSION ${PROJECT_VERSION_MAJOR}
    POSITION_INDEPENDENT_CODE ON
)

# Find dependencies using vcpkg or system
find_package(PkgConfig QUIET)

# Find Armadillo using vcpkg-compatible method or system libraries
if(DEFINED ENV{CIBW_LINUX})
    # For manylinux compatibility, try to use system Armadillo if available
    # But first check if we should force header-only mode for maximum compatibility
    message(STATUS "Configuring Armadillo for manylinux compatibility")
    
    # Force header-only mode to avoid any external library dependencies
    message(STATUS "Using header-only Armadillo for maximum manylinux compatibility")
    add_compile_definitions(ARMA_DONT_USE_BLAS)
    add_compile_definitions(ARMA_DONT_USE_LAPACK)
    add_compile_definitions(ARMA_DONT_USE_HDF5)
    add_compile_definitions(ARMA_DONT_USE_WRAPPER)
    
    find_package(PkgConfig QUIET)
    if(PkgConfig_FOUND)
        pkg_check_modules(ARMADILLO armadillo)
        if(ARMADILLO_FOUND)
            # Only use include directories, not libraries for header-only mode
            target_include_directories(${CMAKE_PROJECT_NAME} PRIVATE ${ARMADILLO_INCLUDE_DIRS})
            message(STATUS "Found system Armadillo via pkgconfig (header-only mode)")
        endif()
    endif()
    
    # Note: We don't link any Armadillo libraries in manylinux mode
    message(STATUS "Armadillo configured for header-only mode")
else()
    # Use vcpkg version for non-manylinux builds
    find_package(Armadillo REQUIRED)
    if(Armadillo_FOUND OR ARMADILLO_FOUND)
        if(TARGET armadillo)
            set(_ldsctrlest_armadillo armadillo)
            message(STATUS "Found Armadillo target")
        else()
            include_directories(${ARMADILLO_INCLUDE_DIRS})
            set(_ldsctrlest_armadillo ${ARMADILLO_LIBRARIES})
            message(STATUS "Found Armadillo libraries: ${ARMADILLO_LIBRARIES}")
        endif()
        message(STATUS "Found Armadillo")
    endif()
endif()

# Link against the specific libraries that vcpkg installs
# Based on the vcpkg output, we know it installs: openblas, lapack-reference
# For manylinux compatibility, avoid vcpkg static libraries that contain C23 symbols
# Use system libraries instead which are compatible with glibc 2.17

if(DEFINED ENV{CIBW_LINUX})
    message(STATUS "Using system libraries for manylinux compatibility instead of vcpkg")
    find_library(OPENBLAS_LIB NAMES openblas PATHS /usr/lib64 /usr/lib/x86_64-linux-gnu NO_DEFAULT_PATH)
    find_library(LAPACK_REF_LIB NAMES lapack PATHS /usr/lib64 /usr/lib/x86_64-linux-gnu NO_DEFAULT_PATH)
    set(_ldsctrlest_blaslapack)
    if(OPENBLAS_LIB)
        list(APPEND _ldsctrlest_blaslapack ${OPENBLAS_LIB})
    endif()
    if(LAPACK_REF_LIB)
        list(APPEND _ldsctrlest_blaslapack ${LAPACK_REF_LIB})
    endif()
elseif(WIN32)
    message(STATUS "Using vcpkg CMake target for OpenBLAS and manually linking lapack.lib for LAPACK on Windows")
    find_package(OpenBLAS CONFIG REQUIRED)
    find_library(LAPACK_REF_LIB NAMES lapack PATHS ${CMAKE_PREFIX_PATH}/lib ${vcpkg_INSTALLED_DIR}/${VCPKG_TARGET_TRIPLET}/lib $ENV{VCPKG_ROOT}/installed/${VCPKG_TARGET_TRIPLET}/lib NO_DEFAULT_PATH)
    set(_ldsctrlest_blaslapack OpenBLAS::OpenBLAS)
    if(LAPACK_REF_LIB)
        list(APPEND _ldsctrlest_blaslapack ${LAPACK_REF_LIB})
        message(STATUS "Found and will link LAPACK reference library: ${LAPACK_REF_LIB}")
    else()
        message(WARNING "LAPACK reference library (lapack.lib) not found! LAPACK routines will be missing.")
        message("")
        message(WARNING "ACTION REQUIRED: LAPACK routines will not be available. To fix:")
        message(WARNING "1. Ensure lapack-reference is listed in vcpkg.json for Windows.")
        message(WARNING "2. Run: vcpkg install lapack-reference:x64-windows")
        message(WARNING "3. Verify lapack.lib exists in one of these paths:")
        message(WARNING "   - ${CMAKE_PREFIX_PATH}/lib")
        message(WARNING "   - ${vcpkg_INSTALLED_DIR}/${VCPKG_TARGET_TRIPLET}/lib")
        message(WARNING "   - $ENV{VCPKG_ROOT}/installed/${VCPKG_TARGET_TRIPLET}/lib")
        message(WARNING "4. If missing, check vcpkg logs and re-run install. If present, re-run CMake.")
        message(WARNING "5. If you still see this message, please report the full CMake log and the contents of your vcpkg install directory.")
        message("")
    endif()
    # Debug output: show compile definitions and linked libraries
    get_target_property(_ldsctrlest_defs ${CMAKE_PROJECT_NAME} COMPILE_DEFINITIONS)
    message(STATUS "ldsctrlest compile definitions: ${_ldsctrlest_defs}")
    get_target_property(_ldsctrlest_libs ${CMAKE_PROJECT_NAME} LINK_LIBRARIES)
    message(STATUS "ldsctrlest linked libraries: ${_ldsctrlest_libs}")
    if(OpenBLAS_FOUND)
        get_target_property(_openblas_lib OpenBLAS::OpenBLAS IMPORTED_LOCATION)
        message(STATUS "OpenBLAS::OpenBLAS IMPORTED_LOCATION: ${_openblas_lib}")
    endif()
endif()

# Search for gfortran in multiple possible locations, prioritizing system paths
# Skip gfortran for manylinux to avoid C23 symbol issues

# Only search for and link gfortran/quadmath on Unix-like systems (not Windows)

set(_ldsctrlest_fortran)
if(NOT DEFINED ENV{CIBW_LINUX} AND NOT WIN32)
    find_library(GFORTRAN_LIB NAMES gfortran libgfortran PATHS /usr/lib64 /lib64 /usr/lib/x86_64-linux-gnu /opt/rh/devtoolset-10/root/usr/lib/gcc/x86_64-redhat-linux/10 /opt/rh/devtoolset-11/root/usr/lib/gcc/x86_64-redhat-linux/11 /opt/rh/devtoolset-9/root/usr/lib/gcc/x86_64-redhat-linux/9 /usr/lib/gcc/x86_64-linux-gnu/10 /usr/lib/gcc/x86_64-linux-gnu/11 /usr/lib/gcc/x86_64-linux-gnu/9 NO_DEFAULT_PATH)
    find_library(QUADMATH_LIB NAMES quadmath libquadmath PATHS /usr/lib64 /lib64 /usr/lib/x86_64-linux-gnu /opt/rh/devtoolset-10/root/usr/lib/gcc/x86_64-redhat-linux/10 /opt/rh/devtoolset-11/root/usr/lib/gcc/x86_64-redhat-linux/11 /opt/rh/devtoolset-9/root/usr/lib/gcc/x86_64-redhat-linux/9 /usr/lib/gcc/x86_64-linux-gnu/10 /usr/lib/gcc/x86_64-linux-gnu/11 /usr/lib/gcc/x86_64-linux-gnu/9 NO_DEFAULT_PATH)
    if(APPLE)
        find_library(ACCELERATE_FRAMEWORK Accelerate)
        if(ACCELERATE_FRAMEWORK)
            list(APPEND _ldsctrlest_fortran ${ACCELERATE_FRAMEWORK})
            message(STATUS "Found and will link Accelerate framework: ${ACCELERATE_FRAMEWORK}")
        else()
            message(STATUS "Accelerate framework not found")
        endif()
    else()
        if(GFORTRAN_LIB)
            list(APPEND _ldsctrlest_fortran ${GFORTRAN_LIB})
            message(STATUS "Found and will link gfortran library: ${GFORTRAN_LIB}")
        else()
            message(STATUS "gfortran library not found; not linking gfortran")
        endif()
        if(QUADMATH_LIB)
            list(APPEND _ldsctrlest_fortran ${QUADMATH_LIB})
            message(STATUS "Found and will link quadmath library: ${QUADMATH_LIB}")
        else()
            message(STATUS "quadmath library not found; not linking quadmath")
        endif()
    endif()
else()
    message(STATUS "Skipping gfortran/quadmath for Windows or manylinux compatibility")
endif()

if(NOT WIN32)
    message(STATUS "Library search results:")
    if(OPENBLAS_LIB)
        target_link_libraries(${CMAKE_PROJECT_NAME} ${OPENBLAS_LIB})
        message(STATUS "Found and linked OpenBLAS library: ${OPENBLAS_LIB}")
    else()
        message(STATUS "OpenBLAS library not found")
    endif()

    if(LAPACK_REF_LIB)
        target_link_libraries(${CMAKE_PROJECT_NAME} ${LAPACK_REF_LIB})
        message(STATUS "Found and linked LAPACK reference library: ${LAPACK_REF_LIB}")
    else()
        message(STATUS "LAPACK reference library not found")
    endif()
endif()

# For manylinux builds, if no external BLAS/LAPACK found, force header-only mode
if(DEFINED ENV{CIBW_LINUX})
    if(NOT OPENBLAS_LIB AND NOT LAPACK_REF_LIB)
        message(STATUS "No external BLAS/LAPACK found for manylinux build - using header-only Armadillo")
        # Force header-only mode by unsetting any BLAS detection
        set(ARMA_USE_BLAS FALSE)
        set(ARMA_USE_LAPACK FALSE)
        add_compile_definitions(ARMA_DONT_USE_BLAS)
        add_compile_definitions(ARMA_DONT_USE_LAPACK)
        add_compile_definitions(ARMA_DONT_USE_HDF5)
        message(STATUS "Configured Armadillo for header-only mode")
    endif()
endif()


# Link Fortran runtime libraries only on Unix-like systems (not Windows)
if(NOT DEFINED ENV{CIBW_LINUX} AND NOT WIN32)
    if(APPLE)
        # macOS: Use Accelerate framework instead of gfortran
        find_library(ACCELERATE_FRAMEWORK Accelerate)
        if(ACCELERATE_FRAMEWORK)
            target_link_libraries(${CMAKE_PROJECT_NAME} ${ACCELERATE_FRAMEWORK})
            message(STATUS "Found and linked Accelerate framework: ${ACCELERATE_FRAMEWORK}")
        else()
            message(STATUS "Accelerate framework not found")
        endif()
    else()
        # Non-macOS Unix platforms: try gfortran/quadmath
        if(GFORTRAN_LIB)
            target_link_libraries(${CMAKE_PROJECT_NAME} ${GFORTRAN_LIB})
            message(STATUS "Found and linked gfortran library: ${GFORTRAN_LIB}")
        else()
            message(STATUS "gfortran library not found; not linking gfortran")
        endif()

        if(QUADMATH_LIB)
            target_link_libraries(${CMAKE_PROJECT_NAME} ${QUADMATH_LIB})
            message(STATUS "Found and linked quadmath library: ${QUADMATH_LIB}")
        else()
            message(STATUS "quadmath library not found; not linking quadmath")
        endif()
    endif()
else()
    message(STATUS "Skipping gfortran and quadmath for Windows or manylinux compatibility")
endif()

# Also link pthread and math libraries which are often needed


set(_ldsctrlest_extra)
find_library(PTHREAD_LIB pthread)
if(PTHREAD_LIB)
    list(APPEND _ldsctrlest_extra ${PTHREAD_LIB})
endif()
if(NOT WIN32)
    list(APPEND _ldsctrlest_extra m)
endif()

# Minimal manylinux compatibility settings
if(CMAKE_SYSTEM_NAME STREQUAL "Linux" AND DEFINED ENV{CIBW_LINUX})
    message(STATUS "Configuring for manylinux compatibility with GCC 10 fixes")
    
    # Add compiler flags to work around GCC 10 + pybind11 static_assert issues
    target_compile_options(${CMAKE_PROJECT_NAME} PRIVATE
        -Wno-deprecated-declarations
        -DPYBIND11_DETAILED_ERROR_MESSAGES
    )
    
    message(STATUS "Applied manylinux compatibility settings with GCC 10 fixes")
endif()

# Find carma for Armadillo-NumPy conversion (already added as subdirectory)
# carma target should be available from add_subdirectory above

# Final unified target_link_libraries call (keyword signature only)
target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE
    ${_ldsctrlest_armadillo}
    ${_ldsctrlest_blaslapack}
    ${_ldsctrlest_fortran}
    ${_ldsctrlest_extra}
    carma::carma
)
message(STATUS "Using carma from submodule")

# Find HDF5 using vcpkg-compatible method (temporarily disabled for manylinux compatibility)
# The __isoc23_strtol symbol from newer glibc is causing issues in manylinux
if(NOT DEFINED ENV{CIBW_LINUX})
    find_package(HDF5 QUIET COMPONENTS C)
    if(HDF5_FOUND)
        if(TARGET hdf5::hdf5)
            target_link_libraries(${CMAKE_PROJECT_NAME} hdf5::hdf5)
        else()
            include_directories(${HDF5_INCLUDE_DIRS})
            target_link_libraries(${CMAKE_PROJECT_NAME} ${HDF5_LIBRARIES})
        endif()
        message(STATUS "Found HDF5")
    endif()
else()
    message(STATUS "HDF5 disabled for manylinux compatibility")
endif()

# Install the main library so it can be found by the Python modules
install(TARGETS ${CMAKE_PROJECT_NAME}
    LIBRARY DESTINATION ldsctrlest
    RUNTIME DESTINATION ldsctrlest)

add_subdirectory(ldsctrlest)