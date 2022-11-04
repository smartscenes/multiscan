#ifndef __HALF_EDGE_H__
#define __HALF_EDGE_H__

#include "trimesh.h"
#include <map>

// reference implementation https://github.com/yig/halfedge.git

class HalfEdge
{
public:
  HalfEdge() = default;
  HalfEdge(const TriMesh* trimesh);

  typedef int index_t;
  typedef std::pair<index_t, index_t> directed_edge;
  typedef std::map<directed_edge, index_t> directed_edge2index_t;

  struct halfedge {
    halfedge() :
      to_v(-1),
      f(-1),
      e(-1),
      opposite(-1),
      next(-1) {}

    index_t to_v;
    index_t f;
    index_t e;
    index_t opposite;
    index_t next;
  };

  void build(const TriMesh* trimesh);
  void clear();

  inline std::vector<edge>& get_undirected_edges() { return undirected_edges;}

  inline halfedge get_halfedge(const index_t i) const { return he_halfedges.at(i); }

  inline halfedge get_half_edge_from_undirected_edge(const index_t& i) const {
    index_t idx = undirected_edge2halfedge[i];
    if (idx == -1) {
      return halfedge();
    }
    
    return he_halfedges[idx];
  }

  inline halfedge get_half_edge_from_directed_edge(const index_t& i, const index_t& j) const {
    directed_edge de = std::make_pair(i, j);
    directed_edge2index_t::const_iterator it = directed_edge2halfedge.find(de);
    if (it == directed_edge2halfedge.end()) {
      return halfedge();
    }
    
    return he_halfedges[it->second];
  }

  inline int get_face_from_undirected_edge(const index_t& i) const {
    return get_half_edge_from_undirected_edge(i).f;
  }

protected:
  std::vector<edge> get_undirected_edges_impl(const std::vector<uint32_t>& faces);
  index_t get_directed_edge2face_index_impl(const directed_edge2index_t& dir_edge2face, index_t va, index_t vb);

private:
  std::vector<edge> undirected_edges;

  std::vector<halfedge> he_halfedges;
  std::vector<index_t> vertex2halfedge;
  std::vector<index_t> face2halfedge;
  std::vector<index_t> undirected_edge2halfedge;
  directed_edge2index_t directed_edge2halfedge;
};

#endif // __HALF_EDGE_H__