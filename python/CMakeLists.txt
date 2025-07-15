cmake_minimum_required(VERSION 3.16)
project(ldsctrlest VERSION 0.9.0 LANGUAGES CXX C)

# Use vcpkg toolchain if available
if(DEFINED CMAKE_TOOLCHAIN_FILE)
    message(STATUS "Using vcpkg toolchain: ${CMAKE_TOOLCHAIN_FILE}")
endif()

# Find Python3, pybind11, and carma
find_package(Python3 COMPONENTS Interpreter Development NumPy REQUIRED)
find_package(pybind11 REQUIRED)
add_subdirectory(carma)

# Add source files and create the main shared library
set(MAIN_PROJECT_DIR ${CMAKE_SOURCE_DIR}/..)
file(GLOB_RECURSE LIB_SOURCES 
    ${MAIN_PROJECT_DIR}/src/*.cpp
    ${MAIN_PROJECT_DIR}/src-fit/*.cpp
)
add_library(${CMAKE_PROJECT_NAME} SHARED ${LIB_SOURCES})

# Set C++ standard and library properties
set_property(TARGET ${CMAKE_PROJECT_NAME} PROPERTY CXX_STANDARD 17)
set_property(TARGET ${CMAKE_PROJECT_NAME} PROPERTY CXX_STANDARD_REQUIRED ON)
set_target_properties(${CMAKE_PROJECT_NAME} PROPERTIES
    VERSION ${PROJECT_VERSION}
    SOVERSION ${PROJECT_VERSION_MAJOR}
    POSITION_INDEPENDENT_CODE ON
)

# Set include directories for the main library
target_include_directories(${CMAKE_PROJECT_NAME} PUBLIC
    ${MAIN_PROJECT_DIR}/include
    ${Python3_INCLUDE_DIRS}
    ${pybind11_INCLUDE_DIRS}
)

# --- Platform-Specific Dependency Linking ---

# For manylinux, use header-only Armadillo for compatibility
if(DEFINED ENV{CIBW_LINUX})
    message(STATUS "Using header-only Armadillo for manylinux.")
    target_compile_definitions(${CMAKE_PROJECT_NAME} PRIVATE ARMA_DONT_USE_BLAS ARMA_DONT_USE_LAPACK)

# For macOS, find Armadillo via vcpkg and link against Apple's native Accelerate framework
elseif(APPLE)
    message(STATUS "Finding Armadillo for macOS and linking against Accelerate.framework...")
    find_package(Armadillo REQUIRED)
    find_library(ACCELERATE_FRAMEWORK Accelerate REQUIRED)
    target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE Armadillo::armadillo ${ACCELERATE_FRAMEWORK})

# For Windows, find Armadillo and let vcpkg handle all dependencies automatically
elseif(WIN32)
    message(STATUS "Finding Armadillo for Windows via vcpkg...")
    find_package(Armadillo REQUIRED)
    target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE Armadillo::armadillo)
endif()

# Link other common dependencies
target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE carma::carma)

# Install the main library
install(TARGETS ${CMAKE_PROJECT_NAME}
    LIBRARY DESTINATION ldsctrlest
    RUNTIME DESTINATION ldsctrlest)

# Add the subdirectory that builds the Python extension modules
add_subdirectory(ldsctrlest)