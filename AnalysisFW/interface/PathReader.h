#ifndef PathReader_h
#define PathReader_h

#include <string>
#include <fstream>
#include <iostream>
#include "Logger.h"

class PathReader{
public:

  //defines possible arguments to be used to
  //perform the reading
  PathReader(){};

  //Fills a queue (templated because we might change 
  //the queue definition to a thread-safe one
  template<typename Q>
  void fill(Q &queue, std::string filename)
  {
    std::ifstream file(filename.c_str());
    if(!file)
    {
      Logger::log().fatal() << "can not open file: " << filename << std::endl;
      throw 42;
    }
    else
    {
      std::string line;
      while ( std::getline(file,line) )
      {
	queue.push(line);
      }
    }
  }
  
private:
};

#endif