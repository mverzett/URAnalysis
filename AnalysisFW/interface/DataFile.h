#ifndef DataFile_h
#define DataFile_h

#include <string>

class DataFile {
public:
  DataFile(std::string);
  std::string path() {return rel_path_;}
  std::string full_path();  

private:
  std::string rel_path_;
};

#endif
