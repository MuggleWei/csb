cmake_minimum_required (VERSION 3.13.5)
project(hello)

include(${CMAKE_CURRENT_LIST_DIR}/../cmake/common.cmake)

find_package(foo REQUIRED)
message("Found foo: ${foo_DIR}")

add_executable(hello ${CMAKE_CURRENT_LIST_DIR}/src/hello.c)
set_target_properties(hello PROPERTIES
	LINKER_LANGUAGE C
	DEBUG_POSTFIX d)
target_link_libraries(hello foo)

if (MSVC OR MINGW)
	set_target_properties(hello
		PROPERTIES
		VS_DEBUGGER_WORKING_DIRECTORY "$(OutDir)"
	)
else()
	if (APPLE)
		set_target_properties(hello
			PROPERTIES
			INSTALL_RPATH "@executable_path/../lib"
		)
	elseif (UNIX)
		set_target_properties(hello
			PROPERTIES
			INSTALL_RPATH "\$ORIGIN/../lib"
		)
	endif()
endif()

include(GNUInstallDirs)
install(TARGETS hello
	RUNTIME DESTINATION "${CMAKE_INSTALL_BINDIR}"
	ARCHIVE DESTINATION "${CMAKE_INSTALL_LIBDIR}"
	LIBRARY DESTINATION "${CMAKE_INSTALL_LIBDIR}")
