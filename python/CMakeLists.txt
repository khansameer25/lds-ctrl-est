add_subdirectory(ldsctrlest)
install(TARGETS base gaussian poisson
        DESTINATION ${CMAKE_INSTALL_PREFIX}/ldsctrlest
        COMPONENT python)
