#ifndef wards_h
#define wards_h

#include "TH1.h"
#include "TDirecotry.h"

class TH1DirectoryWard {
public:
  TH1DirectoryWard() {
  }
  ~TH1DirectoryWard() {
  }
private:
  TDirecotry *dir_;
}

#endif
