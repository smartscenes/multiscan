#include "half_edge.h"
#include <set>
#include <cassert>

using namespace std;

HalfEdge::HalfEdge(const TriMesh* trimesh) 
{
  build(trimesh); 
}

void HalfEdge::build(const TriMesh* trimesh) 
{
  clear();

  vector<uint32_t> faces = trimesh->faces;
  size_t num_faces = trimesh->getFaceNum();
  directed_edge2index_t dir_edge2face;
  for (size_t i = 0; i < num_faces; ++i) {
    const int fbase = 3 * i;
    const uint32_t i1 = faces[fbase];
    const uint32_t i2 = faces[fbase + 1];
    const uint32_t i3 = faces[fbase + 2];

    dir_edge2face[std::make_pair(i1, i2)] = i;
    dir_edge2face[std::make_pair(i2, i3)] = i;
    dir_edge2face[std::make_pair(i3, i1)] = i;
  }

  // get undirected edges from trimesh
  undirected_edges = get_undirected_edges_impl(faces);

  vertex2halfedge.resize(trimesh->getVertSize(), -1);
  face2halfedge.resize(num_faces, -1);
  undirected_edge2halfedge.resize(undirected_edges.size(), -1);
  he_halfedges.reserve(undirected_edges.size() * 2);

  for (size_t ei = 0; ei < undirected_edges.size(); ei++) {
    const edge& e = undirected_edges[ei];

    const index_t he0index = he_halfedges.size();
    he_halfedges.push_back(halfedge());
    halfedge& he0 = he_halfedges.back();

    const index_t he1index = he_halfedges.size();
    he_halfedges.push_back(halfedge());
    halfedge& he1 = he_halfedges.back();

    he0.f = get_directed_edge2face_index_impl(dir_edge2face, e.a, e.b);
    he0.to_v = e.b;
    he0.e = ei;

    he1.f = get_directed_edge2face_index_impl(dir_edge2face, e.b, e.a);
    he1.to_v = e.a;
    he1.e = ei;

    he0.opposite = he1index;
    he1.opposite = he0index;

    assert(directed_edge2halfedge.find(std::make_pair(e.a, e.b)) == directed_edge2halfedge.end());
    assert(directed_edge2halfedge.find(std::make_pair(e.b, e.a)) == directed_edge2halfedge.end());
    directed_edge2halfedge[std::make_pair(e.a, e.b)] = he0index;
    directed_edge2halfedge[std::make_pair(e.b, e.a)] = he1index;

    if (vertex2halfedge[he0.to_v] == -1 || he1.f == -1) {
      vertex2halfedge[he0.to_v] = he0.opposite;
    }
    if (vertex2halfedge[he1.to_v] == -1 || he0.f == -1) {
      vertex2halfedge[he1.to_v] = he1.opposite;
    }

    if (he0.f != -1 && face2halfedge[he0.f] == -1) {
      face2halfedge[he0.f] = he0index;
    }
    if (he1.f != -1 && face2halfedge[he1.f] == -1) {
      face2halfedge[he1.f] = he1index;
    }

    assert(undirected_edge2halfedge[ei] == -1);
    undirected_edge2halfedge[ei] = he0index;
  }

  // assign next half edges
  vector<index_t> boundary_halfedges;
  for (size_t he_idx = 0; he_idx < he_halfedges.size(); he_idx++) {
    halfedge& he = he_halfedges.at(he_idx);
    if (he.f == -1) {
      boundary_halfedges.push_back(he_idx);
      continue;
    }

    const int fbase = 3 * he.f;
    const uint32_t i1 = faces[fbase];
    const uint32_t i2 = faces[fbase + 1];
    const uint32_t i3 = faces[fbase + 2];

    const index_t i = he.to_v;
    index_t j = -1;
    if (i1 == i) j = i2;
    else if (i2 == i) j = i3;
    else if (i3 == i) j = i1;
    assert(j != -1);

    he.next = directed_edge2halfedge[std::make_pair(i, j)];
  }

  std::map<index_t, std::set<index_t>> vertex2outgoing_boundary_he_index;
  for (vector<index_t>::const_iterator he_it = boundary_halfedges.begin(); he_it != boundary_halfedges.end(); ++he_it) {
    const index_t orig_v = he_halfedges[he_halfedges[*he_it].opposite].to_v;
    vertex2outgoing_boundary_he_index[orig_v].insert(*he_it);
    // if (vertex2outgoing_boundary_he_index[orig_v].size() > 1) {
    //   cerr << "Butterfly vertex encountered." << endl;
    // }
  }

  for (vector<index_t>::const_iterator he_it = boundary_halfedges.begin(); he_it != boundary_halfedges.end(); ++he_it) {
    halfedge& he = he_halfedges[*he_it];
    std::set<index_t>& outgoing = vertex2outgoing_boundary_he_index[he.to_v];
    if (!outgoing.empty()) {
      std::set<index_t>::iterator outgoing_he_it = outgoing.begin();
      he.next = *outgoing_he_it;
      outgoing.erase(outgoing_he_it);
    }
  }
}

void HalfEdge::clear() 
{
  undirected_edges.clear();
  he_halfedges.clear();
  vertex2halfedge.clear();
  face2halfedge.clear();
  undirected_edge2halfedge.clear();
  directed_edge2halfedge.clear();
}

std::vector<edge> HalfEdge::get_undirected_edges_impl(const vector<uint32_t>& faces) {
  typedef std::set<std::pair<index_t, index_t>> edge_set_t;
  edge_set_t edge_set;
  size_t num_faces = faces.size()/3;
  for(int i = 0; i < num_faces; ++i) {
    const int fbase = 3 * i;
    const uint32_t i1 = faces[fbase];
    const uint32_t i2 = faces[fbase + 1];
    const uint32_t i3 = faces[fbase + 2];

    edge_set.insert(std::make_pair(std::min(i1, i2), std::max(i1, i2)));
    edge_set.insert(std::make_pair(std::min(i2, i3), std::max(i2, i3)));
    edge_set.insert(std::make_pair(std::min(i3, i1), std::max(i3, i1)));
  }

  std::vector<edge> edges_out(edge_set.size());
  size_t ei = 0;
  for( edge_set_t::const_iterator it = edge_set.begin(); it != edge_set.end(); ++it, ++ei ) {
    edges_out.at(ei).a = it->first;
    edges_out.at(ei).b = it->second;
  }
  return edges_out;
}

HalfEdge::index_t HalfEdge::get_directed_edge2face_index_impl(const directed_edge2index_t& dir_edge2face, index_t va, index_t vb) {
  assert((!dir_edge2face.empty()) && "directed edge to face index map is empty");

  directed_edge2index_t::const_iterator it = dir_edge2face.find(std::make_pair(va, vb));
  if (it == dir_edge2face.end()) {
    assert(dir_edge2face.find(std::make_pair(vb, va)) != dir_edge2face.end());
    return -1;
  }

  return it->second;
}
