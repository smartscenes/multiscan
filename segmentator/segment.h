#ifndef __SEGMENT_H__
#define __SEGMENT_H__

#include <iostream>
#include <unordered_map>
#include <vector>
#include <cassert>
#include <numeric>

#include "trimesh.h"
#include "half_edge.h"

// felzenswalb segmentation (https://cs.brown.edu/~pff/segment/index.html)

// disjoint-set forests using union-by-rank and path compression (sort of).
typedef struct uni_elt {
  int p;
  int rank;
  int size;

  uni_elt() = default;

  uni_elt(int _p, int _rank = 0, int _size = 1) {
    p = _p;
    rank = _rank;
    size = _size;
  }
} uni_elt;

class universe {
public:
  universe(std::vector<int> &vert_indices) {
    num = vert_indices.size();
    for (int i = 0; i < num; i++) {
      int vert_idx = vert_indices[i];
      elts.insert(std::make_pair(vert_idx, uni_elt(vert_idx)));
    }
  }

  ~universe() {
    elts.clear();
  }

  int find(int x) {
    int y = x;
    while (y != elts[y].p)
      y = elts[y].p;
    elts[x].p = y;
    return y;
  }

  void join(int x, int y) {
    if (elts[x].rank > elts[y].rank) {
      elts[y].p = x;
      elts[x].size += elts[y].size;
    } else {
      elts[x].p = y;
      elts[y].size += elts[x].size;
      if (elts[x].rank == elts[y].rank)
        elts[y].rank++;
    }
    num--;
  }

  int size(int x) {
    return elts[x].size;
  }

  int num_sets() const {
    return num;
  }

private:
  std::unordered_map<int, uni_elt> elts;
  int num;
};

inline bool operator<(const edge &a, const edge &b) {
  return a.w < b.w;
}

class Segmentator
{
public:
  Segmentator(TriMesh* trimesh, const bool face_based = false);

  void segment(const float kthr, const int seg_min_size, const float color_weight,
               const float c_kthr, const int c_seg_min_size);

  inline const size_t get_num_segm_coarse() const { return _num_segm_coarse; }
  inline const size_t get_num_segm_fine() const { return _num_segm_fine; }

  inline const std::vector<int> get_segm_coarse() const { return _segm_coarse; }
  inline const std::vector<int> get_segm_fine() const { return _segm_fine; }

protected:
  universe *segment_graph(std::vector<int>& indices, std::vector<edge>& graph, const float c);
  vec3f rgb2hsv(const vec3f &rgb);
  void graph_construct_with_normal(const float weight);
  void graph_construct_with_color(const float weight);
  std::vector<int> segment_impl(std::vector<edge> &graph, std::vector<int> &indices, const float kthr, const int segMinVerts, size_t &num_sets);

private:
  TriMesh *_mesh = nullptr;
  HalfEdge *_half_edge = nullptr;
  bool _face_based;

  std::vector<edge> _graph;

  size_t _num_segm_coarse;
  size_t _num_segm_fine;
  std::vector<int> _segm_coarse;
  std::vector<int> _segm_fine;
};

#endif // __SEGMENT_H__