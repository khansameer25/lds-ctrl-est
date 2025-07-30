cmake_minimum_required(VERSION 3.16)
project(ldsctrlest VERSION 0.9.0 LANGUAGES CXX C)

# Set up paths relative to main project
set(MAIN_PROJECT_DIR ${CMAKE_SOURCE_DIR}/..)
set(CMAKE_MODULE_PATH ${MAIN_PROJECT_DIR}/cmake/Modules ${CMAKE_MODULE_PATH})

# If vcpkg toolchain is available, use it
if(DEFINED CMAKE_TOOLCHAIN_FILE)
    message(STATUS "Using vcpkg toolchain: ${CMAKE_TOOLCHAIN_FILE}")
endif()

# --- START OF FIX ---
# Find Python3 differently for manylinux vs. other platforms
if(DEFINED ENV{CIBW_LINUX})
    # For manylinux, don't request Development components, as they are not
    # always available. Trust the paths from cibuildwheel's env vars.
    message(STATUS "manylinux: Finding Python without Development components.")
    find_package(Python3 COMPONENTS Interpreter NumPy REQUIRED)
else()
    # For other platforms like macOS, find the full development components.
    find_package(Python3 COMPONENTS Interpreter Development NumPy REQUIRED)
endif()
# --- END OF FIX ---

# Find other dependencies
find_package(pybind11 REQUIRED)
find_package(Armadillo REQUIRED)
find_package(HDF5 QUIET COMPONENTS C)

# Add subdirectories for dependencies
add_subdirectory(carma)

# Include directories from the main project itself
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

# Set shared library properties
set_target_properties(${CMAKE_PROJECT_NAME} PROPERTIES
    VERSION ${PROJECT_VERSION}
    SOVERSION ${PROJECT_VERSION_MAJOR}
    POSITION_INDEPENDENT_CODE ON
)

# Add Armadillo dependency robustly, handling both modern target and legacy variable methods
if(TARGET Armadillo::armadillo)
    target_link_libraries(${CMAKE_PROJECT_NAME} PUBLIC Armadillo::armadillo)
else()
    target_include_directories(${CMAKE_PROJECT_NAME} PUBLIC ${ARMADILLO_INCLUDE_DIRS})
    target_link_libraries(${CMAKE_PROJECT_NAME} PUBLIC ${ARMADILLO_LIBRARIES})
endif()

# Link other public and private dependencies
target_link_libraries(${CMAKE_PROJECT_NAME}
    PUBLIC
        carma::carma
    PRIVATE
        m
        ${PTHREAD_LIB}
)

# Platform-specific linking
if(DEFINED ENV{CIBW_LINUX})
    message(STATUS "Finding and linking system BLAS and LAPACK for manylinux...")
    find_package(BLAS REQUIRED)
    find_package(LAPACK REQUIRED)
    target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE ${BLAS_LIBRARIES} ${LAPACK_LIBRARIES})
else()
    message(STATUS "Using vcpkg-provided Accelerate framework for macOS...")
endif()

# Optional HDF5 linking
if(HDF5_FOUND AND NOT DEFINED ENV{CIBW_LINUX})
    target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE HDF5::HDF5)
    message(STATUS "Found and linked HDF5")
endif()

# Minimal manylinux compatibility settings
if(CMAKE_SYSTEM_NAME STREQUAL "Linux" AND DEFINED ENV{CIBW_LINUX})
    message(STATUS "Configuring for manylinux compatibility with GCC 10 fixes")
    target_compile_options(${CMAKE_PROJECT_NAME} PRIVATE
        -Wno-deprecated-declarations
        -DPYBIND11_DETAILED_ERROR_MESSAGES
    )
    message(STATUS "Applied manylinux compatibility settings with GCC 10 fixes")
endif()

# Install the main library so it can be found by the Python modules
install(TARGETS ${CMAKE_PROJECT_NAME}
    LIBRARY DESTINATION ldsctrlest
    RUNTIME DESTINATION ldsctrlest)

# Add the subdirectory that defines the pybind11 modules.
# It will now correctly inherit the PUBLIC include directories from the main library.
add_subdirectory(ldsctrlest)