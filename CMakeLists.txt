cmake_minimum_required(VERSION 3.20)

project(alteruphono
    VERSION 2.0.0
    DESCRIPTION "Sound-change rules applied forwards and backwards, on merkmal"
    LANGUAGES C
)

option(AP_BUILD_TESTS "Build the C tests" ON)
option(AP_BUILD_TOOLS "Build the command-line driver used by the parity harness" ON)
# -Werror is for scripts/check.sh and CI, not for consumers' builds.
option(AP_WERROR "Treat warnings as errors" OFF)
option(AP_BUILD_FUZZERS "Build libFuzzer targets (clang only)" OFF)
set(AP_ENABLE_SANITIZER "" CACHE STRING "Sanitizer for the library and tests: address or undefined")
set(AP_MERKMAL_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../merkmal" CACHE PATH
    "merkmal source tree, used when no installed merkmal is found")

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

if(AP_ENABLE_SANITIZER AND NOT AP_ENABLE_SANITIZER MATCHES "^(address|undefined)$")
    message(FATAL_ERROR "AP_ENABLE_SANITIZER must be empty, address or undefined")
endif()
if(AP_ENABLE_SANITIZER AND MSVC)
    message(FATAL_ERROR "Sanitizer builds are not supported with MSVC")
endif()

# merkmal: an installed package first, else the sibling source tree.
# alteruphono needs mk_system_inventory and mk_unicode_normalize (merkmal master,
# 1a8a90c or later).
find_package(merkmal CONFIG QUIET)
if(NOT merkmal_FOUND)
    if(NOT EXISTS "${AP_MERKMAL_SOURCE_DIR}/CMakeLists.txt")
        message(FATAL_ERROR "merkmal not found: install it or set AP_MERKMAL_SOURCE_DIR")
    endif()
    set(MERKMAL_BUILD_TESTS OFF CACHE BOOL "" FORCE)
    set(MERKMAL_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
    set(MERKMAL_ENABLE_SANITIZER "${AP_ENABLE_SANITIZER}" CACHE STRING "" FORCE)
    add_subdirectory("${AP_MERKMAL_SOURCE_DIR}" "${CMAKE_CURRENT_BINARY_DIR}/merkmal" EXCLUDE_FROM_ALL)
    get_directory_property(merkmal_VERSION DIRECTORY "${AP_MERKMAL_SOURCE_DIR}" DEFINITION PROJECT_VERSION)
endif()
if(NOT merkmal_VERSION)
    message(FATAL_ERROR "cannot determine the merkmal version")
endif()

# Warnings for everything below this line (merkmal is already added above).
if(MSVC)
    add_compile_options(/W4)
    if(AP_WERROR)
        add_compile_options(/WX)
    endif()
else()
    add_compile_options(
        -Wall -Wextra -Wpedantic -Wconversion -Wshadow -Wstrict-prototypes
        -Wmissing-prototypes -Wcast-qual)
    if(AP_WERROR)
        add_compile_options(-Werror)
    endif()
endif()

if(AP_BUILD_FUZZERS)
    if(NOT CMAKE_C_COMPILER_ID MATCHES "Clang")
        message(FATAL_ERROR "AP_BUILD_FUZZERS needs clang")
    endif()
    add_compile_options(-fsanitize=fuzzer-no-link,address,undefined -fno-omit-frame-pointer)
endif()

add_library(alteruphono
    src/util.c
    src/context.c
    src/parser.c
    src/match.c
    src/forward.c
    src/backward.c
    src/model.c
    src/generated/compat1x.c
)
add_library(alteruphono::alteruphono ALIAS alteruphono)
target_include_directories(alteruphono
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src
)
target_link_libraries(alteruphono PUBLIC merkmal::merkmal)
if(NOT MSVC)
    target_link_libraries(alteruphono PUBLIC m)
endif()
set_target_properties(alteruphono PROPERTIES
    C_VISIBILITY_PRESET hidden
    VERSION ${PROJECT_VERSION}
    SOVERSION ${PROJECT_VERSION_MAJOR}
)
target_compile_definitions(alteruphono
    PRIVATE ALTERUPHONO_BUILDING_LIBRARY AP_MERKMAL_VERSION="${merkmal_VERSION}"
    PUBLIC $<$<BOOL:${BUILD_SHARED_LIBS}>:ALTERUPHONO_SHARED>
)
if(AP_ENABLE_SANITIZER)
    set(_ap_san -fsanitize=${AP_ENABLE_SANITIZER} -fno-omit-frame-pointer)
    if(AP_ENABLE_SANITIZER STREQUAL "undefined")
        list(APPEND _ap_san -fno-sanitize-recover=all)
    endif()
    target_compile_options(alteruphono PUBLIC ${_ap_san})
    target_link_options(alteruphono PUBLIC ${_ap_san})
endif()

if(AP_BUILD_TOOLS)
    add_executable(alteruphono-cli tools/cli.c)
    target_link_libraries(alteruphono-cli PRIVATE alteruphono)
    add_executable(bench_engine bench/bench_engine.c)
    target_link_libraries(bench_engine PRIVATE alteruphono)
endif()

if(AP_BUILD_TESTS)
    include(CTest)
    foreach(t context parser forward backward catalogue model)
        add_executable(test_${t} tests/c/test_${t}.c)
        target_link_libraries(test_${t} PRIVATE alteruphono)
        target_compile_options(test_${t} PRIVATE -UNDEBUG)
        target_compile_definitions(test_${t} PRIVATE AP_SOURCE_DIR="${CMAKE_CURRENT_SOURCE_DIR}")
        add_test(NAME ${t} COMMAND test_${t})
    endforeach()
endif()

if(AP_BUILD_FUZZERS)
    foreach(t parse_rule parse_sequence apply model_load)
        add_executable(fuzz_${t} fuzz/fuzz_${t}.c)
        target_link_libraries(fuzz_${t} PRIVATE alteruphono)
        target_link_options(fuzz_${t} PRIVATE -fsanitize=fuzzer,address,undefined)
    endforeach()
endif()

include(GNUInstallDirs)
install(TARGETS alteruphono
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR})
install(FILES include/alteruphono.h DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
