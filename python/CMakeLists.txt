cmake_minimum_required(VERSION 3.16)
project(ldsctrlest VERSION 0.9.0 LANGUAGES CXX C)

# --- Standard Setup ---
# This part is the same as your original file.
set(MAIN_PROJECT_DIR ${CMAKE_SOURCE_DIR}/..)

if(DEFINED CMAKE_TOOLCHAIN_FILE)
    message(STATUS "Using vcpkg toolchain: ${CMAKE_TOOLCHAIN_FILE}")
endif()

find_package(Python3 COMPONENTS Interpreter Development NumPy REQUIRED)
find_package(pybind11 REQUIRED)
add_subdirectory(carma)

# --- Library Definition ---
# Defines the main ldsctrlest shared library.
file(GLOB_RECURSE LIB_SOURCES
    ${MAIN_PROJECT_DIR}/src/*.cpp
    ${MAIN_PROJECT_DIR}/src-fit/*.cpp
)
add_library(${CMAKE_PROJECT_NAME} SHARED ${LIB_SOURCES})
set_property(TARGET ${CMAKE_PROJECT_NAME} PROPERTY CXX_STANDARD 17)
set_property(TARGET ${CMAKE_PROJECT_NAME} PROPERTY CXX_STANDARD_REQUIRED ON)

# --- Include Directories ---
# Explicitly add all necessary include directories to the library target.
# Using PUBLIC ensures that any other target linking against this one (like the
# python modules) will also inherit these include paths.
target_include_directories(${CMAKE_PROJECT_NAME} PUBLIC
    ${MAIN_PROJECT_DIR}/include
    ${Python3_INCLUDE_DIRS}
    ${pybind11_INCLUDE_DIRS}
)

# --- Platform-Specific Dependencies ---
# This is the core of the fix. We handle each OS completely separately.

if(DEFINED ENV{CIBW_LINUX})
    # For manylinux, we compile Armadillo as header-only to maximize compatibility.
    message(STATUS "Configuring for manylinux with header-only Armadillo.")
    target_compile_definitions(${CMAKE_PROJECT_NAME} PRIVATE ARMA_DONT_USE_BLAS ARMA_DONT_USE_LAPACK)

elseif(APPLE)
    # For macOS, vcpkg provides Armadillo, and we link against Apple's native
    # high-performance Accelerate framework for BLAS/LAPACK.
    message(STATUS "Configuring for macOS: Using vcpkg Armadillo + Accelerate.framework.")
    find_package(Armadillo REQUIRED)
    find_library(ACCELERATE_FRAMEWORK Accelerate REQUIRED)
    target_link_libraries(${CMAKE_PROJECT_NAME} PUBLIC Armadillo::armadillo)
    target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE ${ACCELERATE_FRAMEWORK})

elseif(WIN32)
    # For Windows, we let vcpkg handle everything. It provides Armadillo and its
    # dependencies (like OpenBLAS). We just need to add the gfortran runtime libs.
    message(STATUS "Configuring for Windows: Using vcpkg for Armadillo.")
    find_package(Armadillo REQUIRED)
    target_link_libraries(${CMAKE_PROJECT_NAME} PUBLIC Armadillo::armadillo)
    target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE gfortran quadmath)
endif()

# Link other dependencies common to all platforms.
target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE carma::carma pybind11::module)

# --- Installation and Subdirectory ---
# This part is the same as your original file.
install(TARGETS ${CMAKE_PROJECT_NAME}
    LIBRARY DESTINATION ldsctrlest
    RUNTIME DESTINATION ldsctrlest)

add_subdirectory(ldsctrlest)