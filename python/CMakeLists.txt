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

include_directories(${Armadillo_INCLUDE_DIRS})
include_directories(carma/include)

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
    # For manylinux compatibility, use system Armadillo and enable BLAS/LAPACK
    message(STATUS "Configuring Armadillo for manylinux compatibility with BLAS/LAPACK enabled")
    find_package(PkgConfig QUIET)
    if(PkgConfig_FOUND)
        pkg_check_modules(ARMADILLO armadillo)
        if(ARMADILLO_FOUND)
            target_include_directories(${CMAKE_PROJECT_NAME} PRIVATE ${ARMADILLO_INCLUDE_DIRS})
            message(STATUS "Found system Armadillo via pkgconfig")
        endif()
    endif()
else()
    # Use vcpkg version for non-manylinux builds
    find_package(Armadillo REQUIRED)
    if(Armadillo_FOUND OR ARMADILLO_FOUND)
        if(TARGET armadillo)
            target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE armadillo)
            message(STATUS "Found Armadillo target")
        else()
            include_directories(${ARMADILLO_INCLUDE_DIRS})
            target_link_libraries(${CMAKE_PROJECT_NAME} ${ARMADILLO_LIBRARIES})
            message(STATUS "Found Armadillo libraries: ${ARMADILLO_LIBRARIES}")
        endif()
        message(STATUS "Found Armadillo")
    endif()
endif()

# --- START OF MINIMAL CHANGE ---
# This block now handles finding and linking BLAS/LAPACK differently for each platform.
if(DEFINED ENV{CIBW_LINUX})
    # For manylinux, find and link system BLAS/LAPACK.
    # This is more reliable than find_library and will fail loudly if libraries are missing.
    message(STATUS "Finding and linking system BLAS and LAPACK for manylinux...")
    find_package(BLAS REQUIRED)
    find_package(LAPACK REQUIRED)
    target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE ${BLAS_LIBRARIES} ${LAPACK_LIBRARIES})
else()
    # Other platforms (macOS): use original find_library logic.
    message(STATUS "Finding libraries for non-manylinux platform (e.g., macOS)...")
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
    if(OPENBLAS_LIB)
        target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE ${OPENBLAS_LIB})
        message(STATUS "Found and linked OpenBLAS library: ${OPENBLAS_LIB}")
    endif()
    if(LAPACK_REF_LIB)
        target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE ${LAPACK_REF_LIB})
        message(STATUS "Found and linked LAPACK reference library: ${LAPACK_REF_LIB}")
    endif()

    if(APPLE)
        # macOS: Use Accelerate framework
        find_library(ACCELERATE_FRAMEWORK Accelerate)
        if(ACCELERATE_FRAMEWORK)
            target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE ${ACCELERATE_FRAMEWORK})
            message(STATUS "Found and linked Accelerate framework: ${ACCELERATE_FRAMEWORK}")
        endif()
    endif()
endif()
# --- END OF MINIMAL CHANGE ---

# Link pthread and math libraries which are often needed
find_library(PTHREAD_LIB pthread)
if(PTHREAD_LIB)
    target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE ${PTHREAD_LIB})
endif()
target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE m)

# Minimal manylinux compatibility settings
if(CMAKE_SYSTEM_NAME STREQUAL "Linux" AND DEFINED ENV{CIBW_LINUX})
    message(STATUS "Configuring for manylinux compatibility with GCC 10 fixes")
    target_compile_options(${CMAKE_PROJECT_NAME} PRIVATE
        -Wno-deprecated-declarations
        -DPYBIND11_DETAILED_ERROR_MESSAGES
    )
    message(STATUS "Applied manylinux compatibility settings with GCC 10 fixes")
endif()

# Find carma for Armadillo-NumPy conversion
target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE carma::carma)
message(STATUS "Using carma from submodule")

# Find HDF5 using vcpkg-compatible method (disabled for manylinux compatibility)
if(NOT DEFINED ENV{CIBW_LINUX})
    find_package(HDF5 QUIET COMPONENTS C)
    if(HDF5_FOUND)
        if(TARGET hdf5::hdf5)
            target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE hdf5::hdf5)
        else()
            include_directories(${HDF5_INCLUDE_DIRS})
            target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE ${HDF5_LIBRARIES})
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