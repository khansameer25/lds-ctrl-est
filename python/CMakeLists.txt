cmake_minimum_required(VERSION 3.16)
project(ldsctrlest VERSION 0.9.0 LANGUAGES CXX C)

# Use vcpkg toolchain if available
if(DEFINED CMAKE_TOOLCHAIN_FILE)
    message(STATUS "Using vcpkg toolchain: ${CMAKE_TOOLCHAIN_FILE}")
endif()

# Find Python3 and its components
find_package(Python3 COMPONENTS Interpreter Development NumPy REQUIRED)
find_package(pybind11 REQUIRED)

# Add source files and create the main shared library
set(MAIN_PROJECT_DIR ${CMAKE_SOURCE_DIR}/..)
include_directories(${MAIN_PROJECT_DIR}/include)
file(GLOB_RECURSE LIB_SOURCES 
    ${MAIN_PROJECT_DIR}/src/*.cpp
    ${MAIN_PROJECT_DIR}/src-fit/*.cpp
)
add_library(${CMAKE_PROJECT_NAME} SHARED ${LIB_SOURCES})

# Set C++ standard and other properties
set_property(TARGET ${CMAKE_PROJECT_NAME} PROPERTY CXX_STANDARD 17)
set_property(TARGET ${CMAKE_PROJECT_NAME} PROPERTY CXX_STANDARD_REQUIRED ON)
set_target_properties(${CMAKE_PROJECT_NAME} PROPERTIES
    VERSION ${PROJECT_VERSION}
    SOVERSION ${PROJECT_VERSION_MAJOR}
    POSITION_INDEPENDENT_CODE ON
)

# For manylinux, we use a header-only version of Armadillo to avoid library issues.
if(DEFINED ENV{CIBW_LINUX})
    message(STATUS "Using header-only Armadillo for manylinux compatibility.")
    target_compile_definitions(${CMAKE_PROJECT_NAME} PRIVATE ARMA_DONT_USE_BLAS ARMA_DONT_USE_LAPACK)

# For Windows and macOS, we find Armadillo via vcpkg, which handles all dependencies.
else()
    message(STATUS "Finding Armadillo and its dependencies via vcpkg...")
    find_package(Armadillo REQUIRED)
    target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE Armadillo::armadillo)
    message(STATUS "Found and linked Armadillo. vcpkg will handle its dependencies.")
endif()

# Link against pybind11 and carma
add_subdirectory(carma)
target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE pybind11::module carma::carma)

# Install the main library so the Python modules can find it
install(TARGETS ${CMAKE_PROJECT_NAME}
    LIBRARY DESTINATION ldsctrlest
    RUNTIME DESTINATION ldsctrlest)

# Add the subdirectory that builds the actual Python extension modules
add_subdirectory(ldsctrlest)