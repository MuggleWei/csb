cmake_minimum_required (VERSION 3.18.6)
project(hello)

find_package(mugglecpp)

add_executable(hello ${CMAKE_CURRENT_LIST_DIR}/src/main.cpp)
if (APPLE)
    set_target_properties(hello PROPERTIES
        INSTALL_RPATH "@executable_path/../lib"
    )
elseif (UNIX)
    set_target_properties(hello PROPERTIES
        INSTALL_RPATH "\$ORIGIN/../lib"
    )
endif()
target_compile_definitions(hello PRIVATE MUGGLE_HOLD_LOG_MACRO)
target_link_libraries(hello mugglecpp)

include(GNUInstallDirs)
install(TARGETS hello
	RUNTIME DESTINATION "${CMAKE_INSTALL_BINDIR}"
	ARCHIVE DESTINATION "${CMAKE_INSTALL_LIBDIR}"
	LIBRARY DESTINATION "${CMAKE_INSTALL_LIBDIR}")
