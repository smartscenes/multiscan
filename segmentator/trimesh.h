#ifndef TRIMESH_CLASS_H
#define TRIMESH_CLASS_H

#include <algorithm>
#include <cmath>
#include <fstream>
#include <iostream>
#include <vector>

// simple vec3f class
class vec3f {
public:
  float x, y, z;

  vec3f() {
    x = 0;
    y = 0;
    z = 0;
  }

  vec3f(float _x, float _y, float _z) {
    x = _x;
    y = _y;
    z = _z;
  }

  vec3f operator+(const vec3f &o) {
    return vec3f{
        x + o.x, y + o.y, z + o.z
    };
  }

  vec3f operator-(const vec3f &o) {
    return vec3f{
        x - o.x, y - o.y, z - o.z
    };
  }

  vec3f operator*(const vec3f &o) {
    return vec3f{
        x * o.x, y * o.y, z * o.z
    };
  }

  vec3f operator*(const float f) {
    return vec3f{
        x*f, y*f, z*f
    };
  }
};

inline vec3f cross(const vec3f &u, const vec3f &v) {
  vec3f c = {
      u.y * v.z - u.z * v.y, u.z * v.x - u.x * v.z, u.x * v.y - u.y * v.x};
  float n = sqrtf(c.x * c.x + c.y * c.y + c.z * c.z);
  c.x /= n;
  c.y /= n;
  c.z /= n;
  return c;
}

inline vec3f lerp(const vec3f &a, const vec3f &b, const float v) {
  const float u = 1.0f - v;
  return vec3f(v * b.x + u * a.x, v * b.y + u * a.y, v * b.z + u * a.z);
}

// mesh edges
typedef struct {
  float w = 0.0;
  int a, b;
} edge;

// triangle mesh class
class TriMesh {
public:
  TriMesh() = default;

  TriMesh(const std::string &filename);

  ~TriMesh();

// import triangle mesh from local ply or obj file
  void importMesh(const std::string &filename);

// get size of mesh properties
  inline const size_t getVertSize() const {
    return points.size();
  }

  inline const size_t getColorSize() const {
    return colors.size();
  }

  inline const size_t getEdgeSize() const {
    return edges.size();
  }

  inline const size_t getFaceNum() const {
    return faces.size() / 3;
  }

// mesh properties
  std::vector<vec3f> points;
  std::vector<vec3f> normals;
  std::vector<vec3f> face_normals;
  std::vector<vec3f> colors;
  std::vector<edge> edges;
  std::vector<uint32_t> faces;
protected:
  inline bool ends_with(const std::string &value, const std::string &ending) {
    if (ending.size() > value.size()) {
      return false;
    }
    return std::equal(ending.rbegin(), ending.rend(), value.rbegin());
  }

// cast void* data to desired type
  template<typename T, typename V>
  inline void vectype_convert(void *data, V &vec, size_t size) {
    T *tmpData = static_cast<T *>(data);
    vec.assign(tmpData, tmpData + size);
    delete[] tmpData;
  }
};

#endif // TRIMESH_CLASS_H