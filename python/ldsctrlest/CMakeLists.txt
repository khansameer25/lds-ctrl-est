pybind11_add_module(base MODULE base.cpp)
pybind11_add_module(gaussian MODULE gaussian.cpp)
pybind11_add_module(poisson MODULE poisson.cpp)
add_custom_target(python_modules DEPENDS base gaussian poisson)

# need C++14 for CARMA
set_property(TARGET base gaussian poisson PROPERTY CXX_STANDARD 14)
set_property(TARGET base gaussian poisson PROPERTY CXX_STANDARD_REQUIRED ON)

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

# Apply manylinux compatibility settings to Python extension modules
if(CMAKE_SYSTEM_NAME STREQUAL "Linux" AND DEFINED ENV{CIBW_LINUX})
    # Add essential glibc compatibility compile definitions to each Python module
    foreach(target base gaussian poisson)
        target_compile_definitions(${target} PRIVATE
            _GNU_SOURCE=1
            _DEFAULT_SOURCE=1
            # Force C11 standard to avoid C23 symbols
            __STDC_VERSION__=201112L
        )
        target_compile_options(${target} PRIVATE
            -D__GLIBC_MINOR__=17
            # Keep default protections for stability
            -std=gnu++14
        )
    endforeach()
    
    message(STATUS "Applied simplified glibc 2.17 compatibility settings to Python extension modules")
    
    # Force C++14 standard for all Python modules to avoid newer symbols
    set_target_properties(base gaussian poisson PROPERTIES
        CXX_STANDARD 14
        CXX_STANDARD_REQUIRED ON
        CXX_EXTENSIONS ON
    )
endif()

# Install the Python modules to the correct location
install(TARGETS base gaussian poisson
    LIBRARY DESTINATION ldsctrlest
    RUNTIME DESTINATION ldsctrlest)
