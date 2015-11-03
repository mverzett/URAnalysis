#include "DataFile.h"
#include "boost/filesystem.hpp"
#include "Logger.h"
#include <cstdlib>

namespace bf = boost::filesystem;

DataFile::DataFile(std::string path) {
  std::string jobid = std::getenv("jobid"); 
  //search locally
  if(bf::exists( path ) ) {
    rel_path_ = path;
  } else if(bf::exists( "inputs/"+jobid+"/INPUT/"+path ) ) {
    //search in inputs/$jobid/INPUT
    rel_path_ = "inputs/"+jobid+"/INPUT/"+path;    
  } else if(bf::exists( "inputs/data/"+path ) ) {
    //search in inputs/data
    rel_path_ = "inputs/data/"+path;
  } else {
    //throw exception
    Logger::log().error() << "File " << path << " is nowhere to be found!" << std::endl;
    throw 49;
  }
}

std::string DataFile::full_path() {
  return std::string(std::getenv("PATH"))+"/"+rel_path_;
}
