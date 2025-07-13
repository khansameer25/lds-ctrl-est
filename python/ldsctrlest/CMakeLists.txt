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
    # Add strict glibc compatibility compile definitions to Python modules
    target_compile_definitions(base PRIVATE
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
    target_compile_options(base PRIVATE
        -D__GLIBC_MINOR__=17
        -U_FORTIFY_SOURCE
        -D_FORTIFY_SOURCE=0
        -fno-stack-protector
        # Force C11 standard to avoid C23 symbols
        -D__STDC_VERSION__=201112L
        # Explicitly disable newer standards
        -U__STDC_VERSION__
        -D__STDC_VERSION__=201112L
    )
    
    target_compile_definitions(gaussian PRIVATE
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
    target_compile_options(gaussian PRIVATE
        -D__GLIBC_MINOR__=17
        -U_FORTIFY_SOURCE
        -D_FORTIFY_SOURCE=0
        -fno-stack-protector
        # Force C11 standard to avoid C23 symbols
        -D__STDC_VERSION__=201112L
        # Explicitly disable newer standards
        -U__STDC_VERSION__
        -D__STDC_VERSION__=201112L
    )
    
    target_compile_definitions(poisson PRIVATE
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
    target_compile_options(poisson PRIVATE
        -D__GLIBC_MINOR__=17
        -U_FORTIFY_SOURCE
        -D_FORTIFY_SOURCE=0
        -fno-stack-protector
        # Force C11 standard to avoid C23 symbols
        -D__STDC_VERSION__=201112L
        # Explicitly disable newer standards
        -U__STDC_VERSION__
        -D__STDC_VERSION__=201112L
    )
    
    message(STATUS "Applied glibc 2.17 compatibility settings to Python extension modules")
    
    # Force C++14 standard for all Python modules to avoid newer symbols
    set_target_properties(base gaussian poisson PROPERTIES
        CXX_STANDARD 14
        CXX_STANDARD_REQUIRED ON
        CXX_EXTENSIONS ON
    )
    
    # Add C++ standard enforcement to all modules
    target_compile_options(base PRIVATE -std=gnu++14)
    target_compile_options(gaussian PRIVATE -std=gnu++14)
    target_compile_options(poisson PRIVATE -std=gnu++14)
endif()

# Install the Python modules to the correct location
install(TARGETS base gaussian poisson
    LIBRARY DESTINATION ldsctrlest
    RUNTIME DESTINATION ldsctrlest)
