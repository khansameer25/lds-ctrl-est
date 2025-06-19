add_subdirectory(ldsctrlest)
install(TARGETS base gaussian poisson
        DESTINATION ${CMAKE_INSTALL_PREFIX}/ldsctrlest
        COMPONENT python)
install(TARGETS ldsCtrlEst
        LIBRARY
        DESTINATION ${CMAKE_CURRENT_BINARY_DIR}/ldsctrlest
)
