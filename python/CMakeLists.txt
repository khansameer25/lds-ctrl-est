cmake_minimum_required(VERSION 3.16)
project(ldsctrlest VERSION 0.9.0 LANGUAGES CXX C)

# Set up paths relative to main project
set(MAIN_PROJECT_DIR ${CMAKE_SOURCE_DIR}/..)
set(CMAKE_MODULE_PATH ${MAIN_PROJECT_DIR}/cmake/Modules ${CMAKE_MODULE_PATH})

# If vcpkg toolchain is available, use it
if(DEFINED CMAKE_TOOLCHAIN_FILE)
    message(STATUS "Using vcpkg toolchain: ${CMAKE_TOOLCHAIN_FILE}")
endif()

# Find pybind11
find_package(pybind11 REQUIRED)

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

add_subdirectory(ldsctrlest)