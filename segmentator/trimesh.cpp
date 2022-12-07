#include "trimesh.h"

#define TINYOBJLOADER_IMPLEMENTATION

#include "tiny_obj_loader.h"
#include "tinyply.h"

using std::string;
using std::vector;

TriMesh::TriMesh(const string &filename) {
  importMesh(filename);
}

TriMesh::~TriMesh() {
  points.clear();
  normals.clear();
  colors.clear();
  edges.clear();
}

void TriMesh::importMesh(const string &filename) {
  std::cout << "Loading mesh " << filename << std::endl;
  vector<float> verts;
  vector<float> rgbs;
  size_t vertexCount = 0;
  size_t faceCount = 0;
  size_t rgbCount = 0;

  if (ends_with(filename, ".ply") || ends_with(filename, ".PLY")) {
    void *vertsData;
    void *facesData;
    void *rgbData;
    size_t vertexSize = 0;
    size_t faceSize = 0;
    size_t rgbSize = 0;
    size_t vertexInstanceSize = 0;
    size_t faceInstanceSize = 0;
    size_t rgbInstanceSize = 0;

    // Load the geometry from .ply
    std::ifstream ss(filename, std::ios::binary);
    tinyply::PlyFile file(ss);
    vertexCount = file.request_properties_from_element("vertex", {"x", "y", "z"}, vertsData, vertexSize,
                                                       vertexInstanceSize);
    rgbCount = file.request_properties_from_element("vertex", {"red", "green", "blue"}, rgbData, rgbSize,
                                                    rgbInstanceSize);

    // Try getting vertex_indices or vertex_index
    faceCount = file.request_properties_from_element("face", {"vertex_indices"}, facesData, faceSize,
                                                     faceInstanceSize, 3);
    if (faceCount == 0) {
      faceCount = file.request_properties_from_element("face", {"vertex_index"}, facesData, faceSize,
                                                       faceInstanceSize, 3);
    }
    file.read(ss);

    // convert vertices to float type
    if (vertexSize == sizeof(double)) {
      vectype_convert<double, vector < float>>
      (vertsData, verts, vertexInstanceSize);
    } else if (vertexSize == sizeof(float)) {
      vectype_convert<float, vector < float>>
      (vertsData, verts, vertexInstanceSize);
    } else {
      throw std::runtime_error("destination vector is wrongly typed to hold vertex property");
    }

    // convert face indices to uint32_t type
    if (faceSize == sizeof(uint32_t)) {
      vectype_convert<uint32_t, vector < uint32_t>>
      (facesData, faces, faceInstanceSize);
    } else {
      throw std::runtime_error("destination vector is wrongly typed to hold face property");
    }

    if (rgbCount) {
      assert((rgbCount == vertexCount) && "Number of RGB properies doesn't match number of vertices");
      // convert face indices to uint8_t type
      if (rgbSize == sizeof(uint8_t)) {
        vectype_convert<uint8_t, vector < float>>
        (rgbData, rgbs, rgbInstanceSize);
      } else {
        throw std::runtime_error("destination vector is wrongly typed to hold RGB property");
      }
    }
  } else if (ends_with(filename, ".obj") || ends_with(filename, ".OBJ")) {
    // Load the geometry from .obj
    tinyobj::attrib_t attrib;
    vector <tinyobj::shape_t> shapes;
    vector <tinyobj::material_t> materials;
    string err;
    string mtl_basedir = filename.substr(0, filename.find_last_of("/\\") + 1);
    bool ret = tinyobj::LoadObj(&attrib, &shapes, &materials, &err, filename.c_str(), mtl_basedir.c_str(), false);
    if (!err.empty()) {  // `err` may contain warning message.
      std::cerr << err << std::endl;
    }
    if (!ret) {
      exit(1);
    }

    // Keep with original vertices (we don't want them duplicated)
    vertexCount = attrib.vertices.size() / 3;
    for (size_t v = 0; v < attrib.vertices.size(); v++) {
      verts.push_back(attrib.vertices[v]);
    }

    int subFaceCount = 0;
    for (const auto &shape : shapes) {
      const auto &mesh = shape.mesh;
      subFaceCount = mesh.num_face_vertices.size();
      faceCount += subFaceCount;
      for (size_t f = 0; f < subFaceCount; f++) {
        for (size_t v = 0; v < 3; v++) {
          const size_t idx = mesh.indices[3 * f + v].vertex_index;
          faces.push_back(idx);
        }
      }
    }
  }

  printf("Read mesh with vertexCount %lu %lu, faceCount %lu %lu\n",
         vertexCount, verts.size(), faceCount, faces.size());

  // create points, normals, edges, counts vectors
  if (vertexCount > 0) {
    points.resize(vertexCount);
    normals.resize(vertexCount);
  } else {
    throw std::runtime_error("No valid vertex is loaded");
  }
  vector<int> counts(verts.size(), 0);
  const size_t edgesCount = faceCount * 3;

  if (edgesCount > 0) {
    edges.resize(edgesCount);
  } else {
    throw std::runtime_error("No valid facet is loaded");
  }

  if (faceCount > 0) {
    face_normals.resize(faceCount);
  } else {
    throw std::runtime_error("No valid facet is loaded");
  }

  if (rgbCount > 0)
    colors.resize(vertexCount);

  // Compute face normals and smooth into vertex normals
  for (int i = 0; i < faceCount; i++) {
    const int fbase = 3 * i;
    const uint32_t i1 = faces[fbase];
    const uint32_t i2 = faces[fbase + 1];
    const uint32_t i3 = faces[fbase + 2];
    int vbase = 3 * i1;
    vec3f p1(verts[vbase], verts[vbase + 1], verts[vbase + 2]);
    vbase = 3 * i2;
    vec3f p2(verts[vbase], verts[vbase + 1], verts[vbase + 2]);
    vbase = 3 * i3;
    vec3f p3(verts[vbase], verts[vbase + 1], verts[vbase + 2]);
    points[i1] = p1;
    points[i2] = p2;
    points[i3] = p3;
    const int ebase = 3 * i;
    edges[ebase].a = i1;
    edges[ebase].b = i2;
    edges[ebase + 1].a = i1;
    edges[ebase + 1].b = i3;
    edges[ebase + 2].a = i3;
    edges[ebase + 2].b = i2;

    // smoothly blend face normals into vertex normals
    vec3f normal = cross(p2 - p1, p3 - p1);
    face_normals[i] = normal;
    normals[i1] = lerp(normals[i1], normal, 1.0f / (counts[i1] + 1.0f));
    normals[i2] = lerp(normals[i2], normal, 1.0f / (counts[i2] + 1.0f));
    normals[i3] = lerp(normals[i3], normal, 1.0f / (counts[i3] + 1.0f));
    counts[i1]++;
    counts[i2]++;
    counts[i3]++;

    if (rgbCount > 0) {
      int vbase = 3 * i1;
      vec3f c1(rgbs[vbase], rgbs[vbase + 1], rgbs[vbase + 2]);
      vbase = 3 * i2;
      vec3f c2(rgbs[vbase], rgbs[vbase + 1], rgbs[vbase + 2]);
      vbase = 3 * i3;
      vec3f c3(rgbs[vbase], rgbs[vbase + 1], rgbs[vbase + 2]);
      colors[i1] = c1;
      colors[i2] = c2;
      colors[i3] = c3;
    }
  }
}