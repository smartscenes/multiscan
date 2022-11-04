#include <iostream>
#include <unordered_map>
#include <vector>
#include <cassert>
#include <numeric>

#include "segment.h"

#include <rapidjson/document.h>
#include <rapidjson/ostreamwrapper.h>
#include "rapidjson/prettywriter.h"

#include <boost/program_options.hpp>

using std::string;
using std::vector;

namespace po = boost::program_options;

void writeToJSON(const string &filename, const string &scanId,
                 const float kthr, const int segMinVerts, const float colorWeight, const float ckthr,
                 const int cSegMinVerts,
                 const vector<int> &segIndicesCoarse, const vector<int> &segIndicesFine,
                 const bool face_based) {
  rapidjson::Document d;
  d.SetObject();
  rapidjson::Document::AllocatorType &allocator = d.GetAllocator();

  rapidjson::Value id;
  id = rapidjson::StringRef(scanId.c_str());
  d.AddMember("id", id, allocator);
  d.AddMember("version", "hierseg@0.0.2", allocator);

  rapidjson::Value params(rapidjson::kObjectType);
  params.AddMember("kThresh", kthr, allocator);
  params.AddMember("segMinVerts", segMinVerts, allocator);
  params.AddMember("colorWeight", colorWeight, allocator);
  params.AddMember("colorKThresh", ckthr, allocator);
  params.AddMember("colorSegMinVerts", cSegMinVerts, allocator);
  params.AddMember("face_based", face_based, allocator);
  d.AddMember("params", params, allocator);

  rapidjson::Value element_type;
  string element_type_str = face_based ? "triangles" : "vertices";
  element_type = rapidjson::StringRef(element_type_str.c_str());
  rapidjson::Value element_type2(element_type, allocator);

  rapidjson::Value hierarchies(rapidjson::kArrayType);
  rapidjson::Value h1(rapidjson::kObjectType);
  h1.AddMember("name", "fine-coarse", allocator);
  rapidjson::Value levels(rapidjson::kArrayType);
  levels.PushBack("fine", allocator).PushBack("coarse", allocator);
  h1.AddMember("levels", levels, allocator);
  hierarchies.PushBack(h1, allocator);
  d.AddMember("hierarchies", hierarchies, allocator);

  rapidjson::Value segmentation(rapidjson::kArrayType);
  rapidjson::Value s1(rapidjson::kObjectType);
  s1.AddMember("name", "fine", allocator);
  s1.AddMember("elementType", element_type, allocator);

  rapidjson::Value fineIndex(rapidjson::kArrayType);
  fineIndex.Reserve(segIndicesFine.size(), allocator);
  for (int i = 0; i < segIndicesFine.size(); i++)
    fineIndex.PushBack(segIndicesFine[i], allocator);
  s1.AddMember("index", fineIndex, allocator);

  rapidjson::Value coarseIndex(rapidjson::kArrayType);
  rapidjson::Value s2(rapidjson::kObjectType);
  s2.AddMember("name", "coarse", allocator);
  s2.AddMember("elementType", element_type2, allocator);
  coarseIndex.Reserve(segIndicesCoarse.size(), allocator);
  for (int i = 0; i < segIndicesCoarse.size(); i++)
    coarseIndex.PushBack(segIndicesCoarse[i], allocator);
  s2.AddMember("index", coarseIndex, allocator);

  segmentation.PushBack(s1, allocator).PushBack(s2, allocator);
  d.AddMember("segmentation", segmentation, allocator);

  std::ofstream ofs(filename);
  rapidjson::OStreamWrapper osw(ofs);
  rapidjson::PrettyWriter <rapidjson::OStreamWrapper> writer(osw);
  writer.SetFormatOptions(rapidjson::PrettyFormatOptions::kFormatSingleLineArray);
  d.Accept(writer);
  ofs.close();
}

void process(const std::string &meshFile, const float kthr, const int segMinVerts, const float colorWeight,
             const float ckthr, const int cSegMinVerts, const string &scanID, const string &outputFile, const bool face_based) {
  // import mesh from file
  TriMesh *mesh = new TriMesh(meshFile);

  Segmentator* segmentator = new Segmentator(mesh, face_based);
  segmentator->segment(kthr, segMinVerts, colorWeight, ckthr, cSegMinVerts);

  size_t num_segm_coarse = segmentator->get_num_segm_coarse();
  size_t num_segm_fine = segmentator->get_num_segm_fine();
  std::vector<int> segm_coarse = segmentator->get_segm_coarse();
  std::vector<int> segm_fine = segmentator->get_segm_fine();

  // deconstruct triangle mesh instance
  delete segmentator;
  delete mesh;
  // output segmentation result to a json file
  const string baseName = meshFile.substr(0, meshFile.find_last_of("."));
  const int lastslash = meshFile.find_last_of("/");
  string segFile = baseName + "." + std::to_string(kthr) + ".segs.json";
  if (!outputFile.empty())
    segFile = outputFile;
  writeToJSON(segFile, scanID, kthr, segMinVerts, colorWeight, ckthr, cSegMinVerts, segm_coarse, segm_fine, face_based);
  printf("Segmentation written to %s with %lu segments with normals and %lu segments with added colors\n",
         segFile.c_str(), num_segm_coarse, num_segm_fine);
}

int main(int argc, const char **argv) {
  try {
    string meshFile;
    float kthr;
    int segMinVerts;
    float colorWeight;
    float ckthr;
    int cSegMinVerts;
    string scanID;
    string outputFile;
    bool face_based = false;

    po::options_description desc("Segmentator options");
    desc.add_options()
        ("help, h", "help message")
        ("input", po::value<string>(&meshFile)->required(), "set input mesh file")
        ("face_based", po::bool_switch(&face_based), "Segmentation based on faces vs vertices")
        ("kThresh", po::value<float>(&kthr)->default_value(0.01f), "set k threshold")
        ("segMinVerts", po::value<int>(&segMinVerts)->default_value(20), "set minimum segment size")
        ("colorWeight", po::value<float>(&colorWeight)->default_value(0.5f), "set weight for vertex colors")
        ("colorKThresh", po::value<float>(&ckthr)->default_value(0.01f), "set k threshold in second stage")
        ("colorSegMinVerts", po::value<int>(&cSegMinVerts)->default_value(20),
         "set minimum segment size in second stage")
        ("scanID", po::value<string>(&scanID)->default_value("default"), "set the scan ID in the output json file")
        ("output", po::value<string>(&outputFile)->default_value(""), "set the filepath of the output json file");

    po::variables_map vm;
    po::store(po::parse_command_line(argc, argv, desc), vm);

    if (vm.count("help")) {
      std::cout << desc << std::endl;
      return 1;
    }

    po::notify(vm);

    if (vm.count("input")) {
      const string extension = meshFile.substr(meshFile.find_last_of(".")+1);
      if (extension != "obj" && extension != "ply") {
        std::cerr << "Input file should be .ply or .obj" << std::endl;
        return 1;
      }
    }

    if (vm.count("output")) {
      const string extension = outputFile.substr(outputFile.find_last_of(".")+1);
      if (extension != "json") {
        std::cerr << "Output file should be in json format" << std::endl;
        return 1;
      }
    }

    if (face_based)
      printf("Segmenting based on faces\n");
    else
      printf("Segmenting based on vertices\n");

    printf("Segmenting %s with kThresh=%f, segMinVerts=%d, colorWeight=%f, colorKThresh=%f, colorSegMinVerts=%d, ...\n",
           meshFile.c_str(), kthr,
           segMinVerts, colorWeight, ckthr, cSegMinVerts);

    process(meshFile, kthr, segMinVerts, colorWeight, ckthr, cSegMinVerts, scanID, outputFile, face_based);
  } catch (const std::exception &e) {
    std::string error_msg = std::string("Caught a fatal error: ") + std::string(e.what());
#if defined(_WIN32)
    MessageBoxA(nullptr, error_msg.c_str(), NULL, MB_ICONERROR | MB_OK);
#else
    std::cerr << error_msg << std::endl;
#endif
    return -1;
  } catch (...) {
    std::cerr << "Caught an unknown error!" << std::endl;
  }

  return 0;
}
