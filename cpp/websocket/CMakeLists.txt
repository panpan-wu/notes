cmake_minimum_required(VERSION 3.14 FATAL_ERROR)

project(websocket VERSION 0.1)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++14 -pthread -fPIC")
set(CMAKE_VERBOSE_MAKEFILE on)

include(FetchContent)

# third_party: boost
FetchContent_Declare(boost
  URL      https://boostorg.jfrog.io/artifactory/main/release/1.75.0/source/boost_1_75_0.tar.gz
  URL_HASH SHA256=aeb26f80e80945e82ee93e5939baebdca47b9dee80a07d3144be1e1a6a66dd6a
)
FetchContent_MakeAvailable(boost)

add_executable(websocket_server src/websocket_server.cc)
target_include_directories(websocket_server PRIVATE ${boost_SOURCE_DIR})

add_executable(thread_pool src/thread_pool.cc)
target_include_directories(thread_pool PRIVATE ${boost_SOURCE_DIR})

add_executable(websocket_server_1 src/websocket_server_1.cc)
target_include_directories(websocket_server_1 PRIVATE ${boost_SOURCE_DIR})
