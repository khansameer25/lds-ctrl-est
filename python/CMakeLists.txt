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

# Set C++14 standard (required for the project)
set_property(TARGET ${CMAKE_PROJECT_NAME} PROPERTY CXX_STANDARD 14)
set_property(TARGET ${CMAKE_PROJECT_NAME} PROPERTY CXX_STANDARD_REQUIRED ON)

# Set shared library properties for better auditwheel compatibility
set_target_properties(${CMAKE_PROJECT_NAME} PROPERTIES
    VERSION ${PROJECT_VERSION}
    SOVERSION ${PROJECT_VERSION_MAJOR}
    POSITION_INDEPENDENT_CODE ON
)

# Find dependencies using vcpkg or system
find_package(PkgConfig QUIET)

# Find Armadillo using vcpkg-compatible method
find_package(Armadillo REQUIRED)
if(Armadillo_FOUND OR ARMADILLO_FOUND)
    if(TARGET armadillo)
        target_link_libraries(${CMAKE_PROJECT_NAME} armadillo)
        message(STATUS "Found Armadillo target")
    else()
        include_directories(${ARMADILLO_INCLUDE_DIRS})
        target_link_libraries(${CMAKE_PROJECT_NAME} ${ARMADILLO_LIBRARIES})
        message(STATUS "Found Armadillo libraries: ${ARMADILLO_LIBRARIES}")
    endif()
    message(STATUS "Found Armadillo")
endif()

# Link against the specific libraries that vcpkg installs
# Based on the vcpkg output, we know it installs: openblas, lapack-reference
# Try multiple paths to find vcpkg-installed libraries

# Debug: Show what CMAKE_PREFIX_PATH contains
message(STATUS "CMAKE_PREFIX_PATH: ${CMAKE_PREFIX_PATH}")
message(STATUS "vcpkg_INSTALLED_DIR: ${vcpkg_INSTALLED_DIR}")
message(STATUS "VCPKG_TARGET_TRIPLET: ${VCPKG_TARGET_TRIPLET}")

find_library(OPENBLAS_LIB 
    NAMES openblas libopenblas
    PATHS 
        ${CMAKE_PREFIX_PATH}/lib
        ${vcpkg_INSTALLED_DIR}/${VCPKG_TARGET_TRIPLET}/lib
        /project/vcpkg_installed/x64-linux/lib
    NO_DEFAULT_PATH)
find_library(LAPACK_REF_LIB 
    NAMES lapack liblapack
    PATHS 
        ${CMAKE_PREFIX_PATH}/lib
        ${vcpkg_INSTALLED_DIR}/${VCPKG_TARGET_TRIPLET}/lib
        /project/vcpkg_installed/x64-linux/lib
    NO_DEFAULT_PATH)

# Search for gfortran in multiple possible locations, prioritizing system paths
find_library(GFORTRAN_LIB 
    NAMES gfortran libgfortran
    PATHS 
        /usr/lib64
        /lib64
        /usr/lib/x86_64-linux-gnu
        /opt/rh/devtoolset-10/root/usr/lib/gcc/x86_64-redhat-linux/10
        /opt/rh/devtoolset-11/root/usr/lib/gcc/x86_64-redhat-linux/11
        /opt/rh/devtoolset-9/root/usr/lib/gcc/x86_64-redhat-linux/9
        /usr/lib/gcc/x86_64-linux-gnu/10
        /usr/lib/gcc/x86_64-linux-gnu/11
        /usr/lib/gcc/x86_64-linux-gnu/9
    NO_DEFAULT_PATH)

# Also look for libquadmath which is often needed with gfortran
find_library(QUADMATH_LIB 
    NAMES quadmath libquadmath
    PATHS 
        /usr/lib64
        /lib64
        /usr/lib/x86_64-linux-gnu
        /opt/rh/devtoolset-10/root/usr/lib/gcc/x86_64-redhat-linux/10
        /opt/rh/devtoolset-11/root/usr/lib/gcc/x86_64-redhat-linux/11
        /opt/rh/devtoolset-9/root/usr/lib/gcc/x86_64-redhat-linux/9
        /usr/lib/gcc/x86_64-linux-gnu/10
        /usr/lib/gcc/x86_64-linux-gnu/11
        /usr/lib/gcc/x86_64-linux-gnu/9
    NO_DEFAULT_PATH)

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

# Link Fortran runtime libraries in the correct order
if(GFORTRAN_LIB)
    target_link_libraries(${CMAKE_PROJECT_NAME} ${GFORTRAN_LIB})
    message(STATUS "Found and linked gfortran library: ${GFORTRAN_LIB}")
else()
    message(STATUS "gfortran library not found")
    # Try to link by name if not found by path
    target_link_libraries(${CMAKE_PROJECT_NAME} gfortran)
    message(STATUS "Attempting to link gfortran by name")
endif()

if(QUADMATH_LIB)
    target_link_libraries(${CMAKE_PROJECT_NAME} ${QUADMATH_LIB})
    message(STATUS "Found and linked quadmath library: ${QUADMATH_LIB}")
else()
    message(STATUS "quadmath library not found")
    # Try to link by name if not found by path
    target_link_libraries(${CMAKE_PROJECT_NAME} quadmath)
    message(STATUS "Attempting to link quadmath by name")
endif()

# Also link pthread and math libraries which are often needed
find_library(PTHREAD_LIB pthread)
if(PTHREAD_LIB)
    target_link_libraries(${CMAKE_PROJECT_NAME} ${PTHREAD_LIB})
endif()
target_link_libraries(${CMAKE_PROJECT_NAME} m) # math library

# Add specific compiler flags for better manylinux compatibility
if(CMAKE_SYSTEM_NAME STREQUAL "Linux" AND DEFINED ENV{CIBW_LINUX})
    # Set conservative standards for manylinux compatibility
    set_target_properties(${CMAKE_PROJECT_NAME} PROPERTIES
        C_STANDARD 99
        CXX_STANDARD 14
    )
    
    # Add strict glibc compatibility compile definitions to prevent newer symbol usage
    target_compile_definitions(${CMAKE_PROJECT_NAME} PRIVATE
        _GNU_SOURCE=1
        __USE_GNU=1
        _DEFAULT_SOURCE=1
        _POSIX_C_SOURCE=200809L
        _XOPEN_SOURCE=700
        __GLIBC_USE_DEPRECATED_GETS=1
        # Prevent ISO C23 functions by forcing C11 standard
        __STDC_VERSION__=201112L
        _ISOC11_SOURCE=1
    )
    
    # Force older symbol versions and disable newer glibc features
    target_compile_options(${CMAKE_PROJECT_NAME} PRIVATE
        -D__GLIBC_MINOR__=17
        -U_FORTIFY_SOURCE
        -D_FORTIFY_SOURCE=0
        -fno-stack-protector
        # Force C11 standard to avoid C23 symbols
        -D__STDC_VERSION__=201112L
        # Explicitly disable newer standards
        -U__STDC_VERSION__
        -D__STDC_VERSION__=201112L
        # Force C++14 standard to avoid newer symbols
        -std=gnu++14
    )
    
    # Set C++ standard to older version for manylinux compatibility
    set_target_properties(${CMAKE_PROJECT_NAME} PROPERTIES
        CXX_STANDARD 14
        CXX_STANDARD_REQUIRED ON
        CXX_EXTENSIONS ON
    )
    
    message(STATUS "Applied comprehensive manylinux compatibility settings with glibc 2.17 enforcement")
endif()

# Find carma for Armadillo-NumPy conversion (already added as subdirectory)
# carma target should be available from add_subdirectory above
target_link_libraries(${CMAKE_PROJECT_NAME} carma::carma)
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