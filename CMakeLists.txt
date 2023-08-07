cmake_minimum_required(VERSION 3.19)

if (POLICY CMP0048)
    cmake_policy(SET CMP0048 NEW)
endif (POLICY CMP0048)

project(multiscan LANGUAGES C CXX)

option(MTS_BUILD_SEGMENTATOR "Enable building segmentator" ON)
option(MTS_BUILD_INSTANTMESHES "Enable building instant-meshes" ON)
option(MTS_BUILD_OPEN3D "Enable building open3d" ON)
option(MTS_BUILD_MVS_TEXTURING "Enable building mvs-texturing" ON)

option(BUILD_SHARED_LIBS "Build shared libraries" ON)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type for MultiScan" FORCE)
endif()

set(DEPS_CMAKE_BUILD_TYPE "Release" CACHE STRING "Build type for all external libraries")
string(TOLOWER ${DEPS_CMAKE_BUILD_TYPE} DEPS_CMAKE_BUILD_TYPE_LOWERCASE)

if(WIN32)
  set(SCRIPT_EXTENSION bat)
else()
  set(SCRIPT_EXTENSION sh)
endif()

# ==============================================================================
# GNUInstallDirs CMake module
# - Define GNU standard installation directories
# - Provides install directory variables as defined by the GNU Coding Standards.
# ==============================================================================
include(GNUInstallDirs)

if(CMAKE_BUILD_TYPE MATCHES Release)
    message(STATUS "Force CMAKE_INSTALL_DO_STRIP in Release")
    set(CMAKE_INSTALL_DO_STRIP TRUE)
endif()

message(STATUS "----------------------------------------")
message(STATUS "")
message(STATUS "MTS_BUILD_SEGMENTATOR: ${MTS_BUILD_SEGMENTATOR}")
message(STATUS "MTS_BUILD_INSTANTMESHES: ${MTS_BUILD_INSTANTMESHES}")
message(STATUS "MTS_BUILD_OPEN3D: ${MTS_BUILD_OPEN3D}")
message(STATUS "MTS_BUILD_MVS_TEXTURING: ${MTS_BUILD_MVS_TEXTURING}")
message(STATUS "")
message(STATUS "CMAKE_BUILD_TYPE: ${CMAKE_BUILD_TYPE}")
message(STATUS "CMAKE_INSTALL_LIBDIR: ${CMAKE_INSTALL_LIBDIR}")
message(STATUS "CMAKE_INSTALL_PREFIX: ${CMAKE_INSTALL_PREFIX}")
message(STATUS "CMAKE_INSTALL_RPATH: ${CMAKE_INSTALL_RPATH}")
message(STATUS "CMAKE_INSTALL_DO_STRIP: ${CMAKE_INSTALL_DO_STRIP}")
message(STATUS "----------------------------------------")

# ==============================================================================
# Use CMake ExternalProject to build all dependencies
# ==============================================================================
include(ExternalProject)

set(BUILD_DIR "${CMAKE_CURRENT_BINARY_DIR}/external")
set(CMAKE_CORE_BUILD_FLAGS -DCMAKE_PREFIX_PATH=${CMAKE_PREFIX_PATH} -DCMAKE_INCLUDE_PATH=${CMAKE_INCLUDE_PATH} -DCMAKE_LIBRARY_PATH=${CMAKE_LIBRARY_PATH} -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE} -DBUILD_SHARED_LIBS:BOOL=${BUILD_SHARED_LIBS} -DCMAKE_INSTALL_DO_STRIP:BOOL=${CMAKE_INSTALL_DO_STRIP} -DCMAKE_C_COMPILER=${CMAKE_C_COMPILER} -DCMAKE_CXX_COMPILER=${CMAKE_CXX_COMPILER})
# set(CUDA_FLAGS -DCUDA_TOOLKIT_ROOT_DIR=${CMAKE_PREFIX_PATH} -DCMAKE_CUDA_COMPILER=${CMAKE_PREFIX_PATH}/bin/nvcc)

if(MTS_BUILD_OPEN3D)
# Add Open3D
set(OPEN3D_TARGET open3d)
ExternalProject_Add(${OPEN3D_TARGET}
      # 0.13.0
      GIT_REPOSITORY https://github.com/isl-org/Open3D.git
      GIT_TAG v0.13.0
      PREFIX ${BUILD_DIR}
      BUILD_IN_SOURCE 0
      BUILD_ALWAYS 0
      UPDATE_COMMAND ""
      SOURCE_DIR ${CMAKE_CURRENT_BINARY_DIR}/open3d
      BINARY_DIR ${BUILD_DIR}/open3d_build
      INSTALL_DIR ${CMAKE_INSTALL_PREFIX}
      # headless rendering
      CONFIGURE_COMMAND ${CMAKE_COMMAND} ${CMAKE_CORE_BUILD_FLAGS} ${CUDA_FLAGS} -DENABLE_HEADLESS_RENDERING=ON -DBUILD_CUDA_MODULE=ON -DBUILD_CACHED_CUDA_MANAGER=OFF -DBUILD_GUI=OFF -DUSE_SYSTEM_GLEW=OFF -DUSE_SYSTEM_GLFW=OFF -DCMAKE_INSTALL_PREFIX=<INSTALL_DIR> <SOURCE_DIR>
      BUILD_COMMAND $(MAKE) 
      INSTALL_COMMAND cd <BINARY_DIR> && $(MAKE) install-pip-package
      )
set(OPEN3D_CMAKE_FLAGS -DOPEN3D_DIR=${CMAKE_INSTALL_PREFIX})
endif()

if(MTS_BUILD_INSTANTMESHES)
# Add Instant-Meshes
set(INSTANTMESHES_TARGET instant-meshes)
ExternalProject_Add(${INSTANTMESHES_TARGET}
      GIT_REPOSITORY https://github.com/3dlg-hcvc/instant-meshes.git
      GIT_TAG master
      PREFIX ${BUILD_DIR}
      BUILD_IN_SOURCE 0
      BUILD_ALWAYS 0
      UPDATE_COMMAND ""
      SOURCE_DIR ${CMAKE_CURRENT_BINARY_DIR}/instant-meshes
      BINARY_DIR ${BUILD_DIR}/instant-meshes_build
      INSTALL_DIR ${CMAKE_INSTALL_PREFIX}
      CONFIGURE_COMMAND ${CMAKE_COMMAND} ${CMAKE_CORE_BUILD_FLAGS} -DBUILD_GUI=OFF -DCMAKE_INSTALL_PREFIX=<INSTALL_DIR> <SOURCE_DIR>
      BUILD_COMMAND $(MAKE)
      INSTALL_COMMAND mkdir -p <INSTALL_DIR>/bin && cp <BINARY_DIR>/Instant\ Meshes <INSTALL_DIR>/bin/Instant\ Meshes
      )
set(INSTANTMESHES_CMAKE_FLAGS -DINSTANTMESHES_DIR=${CMAKE_INSTALL_PREFIX} -DINSTANTMESHES_SRC_DIR=${CMAKE_CURRENT_BINARY_DIR}/instant-meshes)
endif()

if(MTS_BUILD_MVS_TEXTURING)

# Add MVS-Texturing
set(MVSTEXTURING_TARGET mvstexturing)
set(TBB_CMAKE_FLAGS -DTBB_INCLUDE_DIRS:PATH=${CMAKE_INCLUDE_PATH} -DTBB_LIBRARIES=${CMAKE_LIBRARY_PATH}/libtbb.so)
ExternalProject_Add(${MVSTEXTURING_TARGET}
      GIT_REPOSITORY git@github.com:3dlg-hcvc/mvs-texturing.git
      GIT_TAG master
      PREFIX ${BUILD_DIR}
      BUILD_IN_SOURCE 0
      BUILD_ALWAYS 0
      UPDATE_COMMAND ""
      SOURCE_DIR ${CMAKE_CURRENT_BINARY_DIR}/mvs-texturing
      BINARY_DIR ${BUILD_DIR}/mvs-texturing_build
      INSTALL_DIR ${CMAKE_INSTALL_PREFIX}
      CONFIGURE_COMMAND ${CMAKE_COMMAND} ${CMAKE_CORE_BUILD_FLAGS} ${TBB_CMAKE_FLAGS} -DCMAKE_INSTALL_PREFIX=<INSTALL_DIR> <SOURCE_DIR>
      BUILD_COMMAND $(MAKE)
      )
set(MVS_TEXTURING_CMAKE_FLAGS -DMVS_TEXTURING_DIR=${CMAKE_INSTALL_PREFIX})
endif()

if(MTS_BUILD_SEGMENTATOR)
set(SEGMENTATOR_TARGET segmentator)
ExternalProject_Add(${SEGMENTATOR_TARGET}
       PREFIX ${BUILD_DIR}
       BUILD_IN_SOURCE 0
       BUILD_ALWAYS 0
       SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/segmentator
       BINARY_DIR ${BUILD_DIR}/segmentator_build
       INSTALL_DIR ${CMAKE_INSTALL_PREFIX}
       CONFIGURE_COMMAND ${CMAKE_COMMAND} ${CMAKE_CORE_BUILD_FLAGS} -DCMAKE_INSTALL_PREFIX:PATH=<INSTALL_DIR> <SOURCE_DIR>
       BUILD_COMMAND $(MAKE)
       )
endif()

install(
        FILES README.md
        DESTINATION ${CMAKE_INSTALL_DATADIR}/doc
)
