cmake_minimum_required(VERSION 3.16)
project(alife_core VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Статическая библиотека alife_core
add_library(alife_core STATIC
    src/version.cpp
    src/rng.cpp
)

target_include_directories(alife_core PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Исполняемый файл alife_headless
add_executable(alife_headless
    src/headless_main.cpp
)
target_link_libraries(alife_headless PRIVATE alife_core)

# Тесты
enable_testing()

add_executable(test_version tests/test_version.cpp)
target_link_libraries(test_version PRIVATE alife_core)

add_executable(test_rng tests/test_rng.cpp)
target_link_libraries(test_rng PRIVATE alife_core)

add_test(NAME test_version COMMAND test_version)
add_test(NAME test_rng COMMAND test_rng)
