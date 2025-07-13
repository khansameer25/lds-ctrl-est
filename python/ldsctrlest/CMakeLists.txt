pybind11_add_module(base MODULE base.cpp)
pybind11_add_module(gaussian MODULE gaussian.cpp)
pybind11_add_module(poisson MODULE poisson.cpp)
add_custom_target(python_modules DEPENDS base gaussian poisson)

# need C++17 for pybind11 compatibility
target_compile_features(base PUBLIC cxx_std_17)
target_compile_features(gaussian PUBLIC cxx_std_17)
target_compile_features(poisson PUBLIC cxx_std_17)

target_compile_definitions(base PRIVATE VERSION_INFO=${PROJECT_VERSION})
target_compile_definitions(gaussian PRIVATE VERSION_INFO=${PROJECT_VERSION})
target_compile_definitions(poisson PRIVATE VERSION_INFO=${PROJECT_VERSION})

# carma already linked to main project
target_link_libraries(base PUBLIC ${CMAKE_PROJECT_NAME})
target_link_libraries(gaussian PUBLIC ${CMAKE_PROJECT_NAME})
target_link_libraries(poisson PUBLIC ${CMAKE_PROJECT_NAME})

# Set RPATH so the extension modules can find the main library
if(APPLE)
    set_target_properties(base gaussian poisson PROPERTIES
        INSTALL_RPATH "@loader_path"
        BUILD_WITH_INSTALL_RPATH TRUE)
else()
    # Linux: use $ORIGIN instead of @loader_path
    set_target_properties(base gaussian poisson PROPERTIES
        INSTALL_RPATH "$ORIGIN"
        BUILD_WITH_INSTALL_RPATH TRUE)
endif()

# Minimal manylinux compatibility for Python extension modules
if(CMAKE_SYSTEM_NAME STREQUAL "Linux" AND DEFINED ENV{CIBW_LINUX})
    message(STATUS "Applying manylinux settings to Python extension modules with GCC 10 fixes")
    
    # Ensure C++17 standard and add GCC 10 compatibility flags
    target_compile_features(base PUBLIC cxx_std_17)
    target_compile_features(gaussian PUBLIC cxx_std_17)
    target_compile_features(poisson PUBLIC cxx_std_17)
    
    # Add compiler flags to work around GCC 10 + pybind11 issues
    foreach(target base gaussian poisson)
        target_compile_options(${target} PRIVATE
            -Wno-deprecated-declarations
            -DPYBIND11_DETAILED_ERROR_MESSAGES
        )
    endforeach()
endif()

# Install the Python modules to the correct location
install(TARGETS base gaussian poisson
    LIBRARY DESTINATION ldsctrlest
    RUNTIME DESTINATION ldsctrlest)
