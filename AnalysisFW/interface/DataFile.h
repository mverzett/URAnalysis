#ifndef DataFile_h
#define DataFile_h

#include <string>

class DataFile {
public:
  DataFile():
    rel_path_() {}
  DataFile(std::string);
  std::string path() const {return rel_path_;}
  std::string full_path() const;  

private:
  std::string rel_path_;
};

#endif
