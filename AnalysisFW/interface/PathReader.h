#ifndef PathReader_h
#define PathReader_h

#include <string>
#include <fstream>
#include <iostream>
#include "URAnalysis/AnalysisFW/interface/Logger.h"

class PathReader{
public:

  //defines possible arguments to be used to
  //perform the reading
  PathReader(){};

  //Fills a queue (templated because we might change 
  //the queue definition to a thread-safe one
  template<typename Q>
  long int fill(Q &queue, std::string filename, size_t njob = 1, size_t jobs = 1)
  {
    std::ifstream file(filename.c_str());
    long int counter = 0;
    if(!file)
    {
	    Logger::log().fatal() << "can not open file: " << filename << std::endl;
	    throw 42;
    }
    else
    {
	    using namespace std;
	    vector<string> filenames;
	    string line;
	    while(getline(file,line))
	    {
		    filenames.push_back(line);
	    }
	    jobs = min(jobs, filenames.size());
	    if(njob >= jobs)
	    {
		    Logger::log().fatal() << "jobnumber ("<< njob <<") is larger than number of files: " << 
					filenames.size() << std::endl;
		    throw 42;
	    }
	    size_t mod = filenames.size() % jobs;
	    size_t filesperjob = filenames.size() / jobs;
	    size_t jobmin = njob*filesperjob + min(mod, njob);
	    size_t jobmax = (njob+1)*filesperjob + min(mod, njob+1);
	    for(size_t nf = jobmin ; nf < jobmax ; ++nf)
	    {
		    queue.push(filenames[nf]);
		    counter++;
	    }

	    //while ( std::getline(file,line) )
	    //{
	    //  counter++;
	    //  queue.push(line);
	    //}
    }
    return counter;
  }
  
private:
};

#endif
