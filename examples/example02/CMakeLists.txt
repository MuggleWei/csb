cmake_minimum_required (VERSION 3.13.5)
project(inner_var)

include(${CMAKE_CURRENT_LIST_DIR}/../cmake/common.cmake)

add_executable(inner_var ${CMAKE_CURRENT_LIST_DIR}/src/hello.c)