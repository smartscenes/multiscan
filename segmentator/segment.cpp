#include "segment.h"

using namespace std;

#define PI 3.14159265358979323846

Segmentator::Segmentator(TriMesh* trimesh, const bool face_based) {
  _mesh = trimesh;
  _half_edge = new HalfEdge(_mesh);
  _face_based = face_based;
}

void Segmentator::segment(const float kthr, const int seg_min_size, const float color_weight,
                          const float c_kthr, const int c_seg_min_size) {
  graph_construct_with_normal(1.0);
  std::vector<int> indices;
  if (_face_based)
    indices.resize(_mesh->getFaceNum());
  else
    indices.resize(_mesh->getVertSize());
  
  std::iota(indices.begin(), indices.end(), 0);
  _segm_coarse = segment_impl(_graph, indices, kthr, seg_min_size, _num_segm_coarse);
  _segm_fine = _segm_coarse;

  graph_construct_with_color(color_weight);

  std::unordered_map<int, vector<int>> comp_vert_indices;
  for (int i = 0; i < _segm_fine.size(); i++) {
    auto entry = comp_vert_indices.find(_segm_fine[i]);
    if (entry != comp_vert_indices.end())
      entry->second.emplace_back(i);
    else
      comp_vert_indices.insert(std::make_pair(_segm_fine[i], vector<int> {i}));
  }

  std::unordered_map<int, vector<edge>> comp_edges;
  for (int i = 0; i < _graph.size(); i++) {
    int center = _segm_fine[_graph[i].a];
    if (center == _segm_fine[_graph[i].b]) {
      auto entry = comp_edges.find(center);
      if (entry != comp_edges.end())
        entry->second.emplace_back(_graph[i]);
      else {
        comp_edges.insert(std::make_pair(center, vector<edge> {_graph[i]}));
      }
    }
  }

  int total_vertices = 0;
  _num_segm_fine = 0;
  for (auto iter = comp_vert_indices.begin(); iter != comp_vert_indices.end(); ++iter) {
    int center = iter->first;
    int num_vertices = iter->second.size();

    auto segm = comp_edges.find(center);
    if (segm != comp_edges.end()) {
      size_t num_segm_each;
      // std::cout << "num_vertices " << num_vertices << std::endl;
      // std::cout << "Edges " << segm->second.size() << std::endl;
      const vector<int> comps_each = segment_impl(segm->second, iter->second, c_kthr, c_seg_min_size, num_segm_each);
      for (int i = 0; i < comps_each.size(); i++) {
        _segm_fine[iter->second[i]] = comps_each[i];
      }
      _num_segm_fine += num_segm_each;
    } else
      std::cerr <<"No edge in a segment" << std::endl;
    total_vertices += num_vertices;
  }

  if (_face_based)
    assert((total_vertices == _mesh->getFaceNum()) && "Number of faces doesn't match after segmentation");
  else
    assert((total_vertices == _mesh->getVertSize()) && "Number of vertices doesn't match after segmentation");
}

universe* Segmentator::segment_graph(std::vector<int>& indices, std::vector<edge>& graph, const float c) {
  // graph G =(V, E)
  size_t num_vertices = indices.size();
  size_t num_edges = graph.size();
  std::sort(graph.begin(), graph.end()); // sort edges by weight
  universe *u = new universe(indices);  // make a disjoint-set forest
  std::unordered_map<int, float> threshold;
  for (int i = 0; i < num_vertices; i++) {
    threshold.insert(std::make_pair(indices[i], c));
  }
  // for each edge, in non-decreasing weight order
  for (int i = 0; i < num_edges; i++) {
    edge *pedge = &graph[i];
    // components conected by this edge
    int a = u->find(pedge->a);
    int b = u->find(pedge->b);
    if (a != b) {
      if ((pedge->w <= threshold[a]) && (pedge->w <= threshold[b])) {
        u->join(a, b);
        a = u->find(a);
        threshold[a] = pedge->w + (c / u->size(a));
      }
    }
  }
  threshold.clear();
  return u;
}

vec3f Segmentator::rgb2hsv(const vec3f &rgb) {
  float r = rgb.x / 255.0;
  float g = rgb.y / 255.0;
  float b = rgb.z / 255.0;

  float cmax = std::max(r, std::max(g, b));
  float cmin = std::min(r, std::min(g, b));
  float d = cmax - cmin;

  int h = 0, s = 0, v = int(cmax) * 100;
  if (cmax == cmin)
    h = 0;
  else if (cmax == r)
    h = (int) (60.0 * (g - b) / d + 360.0) % 360;
  else if (cmax == g)
    h = (int) (60.0 * (b - r) / d + 120.0) % 360;
  else if (cmax == b)
    h = (int) (60.0 * (r - g) / d + 240.0) % 360;

  if (cmax == 0)
    s = 0;
  else
    s = (int) (d / cmax * 100.0);

  return vec3f(h, s, v);
}

void Segmentator::graph_construct_with_color(const float weight) {
  // vector<edge>& edges = _half_edge->get_undirected_edges();
  vector<edge>& edges = _mesh->edges;

  int color_count = _mesh->getColorSize();
  if (color_count <= 0)
    std::cerr << "No color property exists in the mesh" << std::endl;
  else {
    //std::cout << "Constructing edge graph based on mesh connectivity..." << std::endl;
    for (int i = 0; i < _graph.size(); i++) {
      vec3f rgb1, rgb2;

      if (_face_based) {
        HalfEdge::halfedge he = _half_edge->get_half_edge_from_directed_edge(edges[i].a, edges[i].b);
        int f1 = he.f;
        int f2 = _half_edge->get_halfedge(he.opposite).f;

        _graph[i].a = f1;
        _graph[i].b = f2;

        int fbase = 3 * f1;
        uint32_t i1 = _mesh->faces[fbase];
        uint32_t i2 = _mesh->faces[fbase + 1];
        uint32_t i3 = _mesh->faces[fbase + 2];
        rgb1 = _mesh->colors[i1]*_mesh->colors[i1] + _mesh->colors[i2]*_mesh->colors[i2] + _mesh->colors[i3]*_mesh->colors[i3];
        rgb1 = rgb1 * (1.0 / 3.0);
        rgb1.x = sqrtf(rgb1.x);
        rgb1.y = sqrtf(rgb1.y);
        rgb1.z = sqrtf(rgb1.z);

        fbase = 3 * f2;
        i1 = _mesh->faces[fbase];
        i2 = _mesh->faces[fbase + 1];
        i3 = _mesh->faces[fbase + 2];
        rgb2 = _mesh->colors[i1]*_mesh->colors[i1] + _mesh->colors[i2]*_mesh->colors[i2] + _mesh->colors[i3]*_mesh->colors[i3];
        rgb2 = rgb2 * (1.0 / 3.0);
        rgb2.x = sqrtf(rgb2.x);
        rgb2.y = sqrtf(rgb2.y);
        rgb2.z = sqrtf(rgb2.z);
      }
      else{
        int a = edges[i].a;
        int b = edges[i].b;

        _graph[i].a = a;
        _graph[i].b = b;

        rgb1 = _mesh->colors[a];
        rgb2 = _mesh->colors[b];
      }

      float dc = 0.0;
      // reference Toscana2016 https://arxiv.org/pdf/1605.03746.pdf
      // weight calculated from hsv
      vec3f c1 = rgb2hsv(rgb1);
      vec3f c2 = rgb2hsv(rgb2);
      float kdv = 4.5, kds = 0.1;
      float dv = kdv * fabs(c1.z - c2.z);
      float dh = fabs(c1.x - c2.x);
      float theta = dh;
      if (dh >= 180)
        theta = 360.0 - dh;
      theta *= PI / 180.0;
      float ds = kds * sqrt(c1.y * c1.y + c2.y * c2.y - 2.0 * cos(theta) * c1.y * c2.y);
      dc = sqrt(dv * dv + ds * ds) / sqrt(kdv * kdv + kds * kds);
      dc = log2(1 + dc);
      _graph[i].w = (1.0 - weight) * _graph[i].w + weight * dc;
    }
  }
  //std::cout << "Constructed graph" << std::endl;
}

void Segmentator::graph_construct_with_normal(const float weight) {
  // vector<edge>& edges = _half_edge->get_undirected_edges();
  vector<edge>& edges = _mesh->edges;
  _graph.resize(edges.size());

  std::vector<vec3f> normals;
  if (_face_based)
    normals = _mesh->face_normals;
  else
    normals = _mesh->normals;

  size_t normal_count = normals.size();
  if (normal_count <= 0)
    std::cerr << "No normal property exists in the mesh" << std::endl;
  else {
    //std::cout << "Constructing edge graph based on mesh connectivity..." << std::endl;
    for (int i = 0; i < _graph.size(); i++) {
      vec3f n1, n2;
      vec3f p1, p2;
      if (_face_based) {
        HalfEdge::halfedge he = _half_edge->get_half_edge_from_directed_edge(edges[i].a, edges[i].b);
        int f1 = he.f;
        int f2 = _half_edge->get_halfedge(he.opposite).f;

        // Skip boundary face
        if (f1 == -1 || f2 == -1) {
          continue;
        }

        _graph[i].a = f1;
        _graph[i].b = f2;

        n1 = normals[f1];
        n2 = normals[f2];
        int fbase = 3 * f1;
        uint32_t i1 = _mesh->faces[fbase];
        uint32_t i2 = _mesh->faces[fbase + 1];
        uint32_t i3 = _mesh->faces[fbase + 2];
        p1 = _mesh->points[i1] + _mesh->points[i2] + _mesh->points[i3];
        p1 = p1 * (1.0 / 3.0);

        fbase = 3 * f2;
        i1 = _mesh->faces[fbase];
        i2 = _mesh->faces[fbase + 1];
        i3 = _mesh->faces[fbase + 2];
        p2 = _mesh->points[i1] + _mesh->points[i2] + _mesh->points[i3];
        p2 = p2 * (1.0 / 3.0);
      } else {
        int a = edges[i].a;
        int b = edges[i].b;

        _graph[i].a = a;
        _graph[i].b = b;

        n1 = normals[a];
        n2 = normals[b];
        p1 = _mesh->points[a];
        p2 = _mesh->points[b];
      }

      float dx = p2.x - p1.x;
      float dy = p2.y - p1.y;
      float dz = p2.z - p1.z;
      float dd = sqrtf(dx * dx + dy * dy + dz * dz);
      dx /= dd;
      dy /= dd;
      dz /= dd;
      float dot = n1.x * n2.x + n1.y * n2.y + n1.z * n2.z;
      float dot2 = n2.x * dx + n2.y * dy + n2.z * dz;
      float ww = 1.0f - dot;
      if (dot2 > 0) {
        ww = ww * ww;
      }  // make it much less of a problem if convex regions have normal difference
      _graph[i].w = (1.0 - weight) * _graph[i].w + weight * ww;
    }
  }
  //std::cout << "Constructed graph" << std::endl;
}

vector<int>
Segmentator::segment_impl(vector<edge> &graph, vector<int> &indices, const float kthr, const int segMinVerts, size_t &num_sets) {
  // Segment!
  universe *u = segment_graph(indices, graph, kthr);
  // std::cout << "Segmented" << std::endl;

  // Joining small segments
  for (int j = 0; j < graph.size(); j++) {
    int a = u->find(graph[j].a);
    int b = u->find(graph[j].b);
    if ((a != b) && ((u->size(a) < segMinVerts) || (u->size(b) < segMinVerts))) {
      u->join(a, b);
    }
  }

  // Return segment indices as vector
  size_t vertex_count = indices.size();
  vector<int> out_comps(vertex_count);
  for (int q = 0; q < vertex_count; q++) {
    out_comps[q] = u->find(indices[q]);
  }

  num_sets = u->num_sets();
  delete u;
  return out_comps;
}
