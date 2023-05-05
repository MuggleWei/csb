cmake_minimum_required (VERSION 3.13.5)
project(hello)

include(${CMAKE_CURRENT_LIST_DIR}/../cmake/common.cmake)

find_package(ZLIB REQUIRED)
message("Found zlib version: ${ZLIB_VERSION}")
message("Found zlib include dirs: ${ZLIB_INCLUDE_DIRS}")
message("Found zlib libraries: ${ZLIB_LIBRARIES}")

add_executable(hello ${CMAKE_CURRENT_LIST_DIR}/src/hello.c)
set_target_properties(hello PROPERTIES
	LINKER_LANGUAGE C
	DEBUG_POSTFIX d)
target_link_libraries(hello ${ZLIB_LIBRARIES})

include(GNUInstallDirs)
install(TARGETS hello
	RUNTIME DESTINATION "${CMAKE_INSTALL_BINDIR}"
	ARCHIVE DESTINATION "${CMAKE_INSTALL_LIBDIR}"
	LIBRARY DESTINATION "${CMAKE_INSTALL_LIBDIR}")
