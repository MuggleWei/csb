cmake_minimum_required (VERSION 3.13.5)
project(built_in_var)

include(${CMAKE_CURRENT_LIST_DIR}/../cmake/common.cmake)

add_executable(hello ${CMAKE_CURRENT_LIST_DIR}/src/hello.c)

include(GNUInstallDirs)
install(TARGETS hello
	RUNTIME DESTINATION "${CMAKE_INSTALL_BINDIR}"
	ARCHIVE DESTINATION "${CMAKE_INSTALL_LIBDIR}"
	LIBRARY DESTINATION "${CMAKE_INSTALL_LIBDIR}")