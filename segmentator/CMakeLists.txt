cmake_minimum_required(VERSION 3.1 FATAL_ERROR)
set(CMAKE_CXX_STANDARD 11)
project(Segmentator)

# include RapidJson
find_package(RapidJSON)
include_directories(${RAPIDJSON_INCLUDE_DIRS})

# include Boost
set(Boost_USE_STATIC_LIBS OFF)
find_package(Boost 1.60 QUIET COMPONENTS program_options REQUIRED)

if (Boost_FOUND)
    include_directories(${Boost_INCLUDE_DIR})
    set(SOURCES segmentator.cpp tinyply.cpp trimesh.cpp half_edge.cpp segment.cpp)
    add_executable(segmentator ${SOURCES})
    target_link_libraries(segmentator ${Boost_LIBRARIES})
endif ()

install(TARGETS segmentator ${DCMAKE_INSTALL_PREFIX})