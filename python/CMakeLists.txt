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
    else()
        include_directories(${ARMADILLO_INCLUDE_DIRS})
        target_link_libraries(${CMAKE_PROJECT_NAME} ${ARMADILLO_LIBRARIES})
    endif()
    message(STATUS "Found Armadillo")
endif()

# Explicitly find and link LAPACK and BLAS (required by Armadillo)
find_package(LAPACK REQUIRED)
find_package(BLAS REQUIRED)
target_link_libraries(${CMAKE_PROJECT_NAME} ${LAPACK_LIBRARIES} ${BLAS_LIBRARIES})

# Find carma for Armadillo-NumPy conversion (already added as subdirectory)
# carma target should be available from add_subdirectory above
target_link_libraries(${CMAKE_PROJECT_NAME} carma::carma)
message(STATUS "Using carma from submodule")

# Find HDF5 using vcpkg-compatible method
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

# Install the main library so it can be found by the Python modules
install(TARGETS ${CMAKE_PROJECT_NAME}
    LIBRARY DESTINATION ldsctrlest
    RUNTIME DESTINATION ldsctrlest)

add_subdirectory(ldsctrlest)