#ifndef ProgressBar_h
#define ProgressBar_h

//
// Simple class to provide a ProgressBar, because C++ 
// does not have any nice libs
//

#include <atomic>

#include <stdio.h>
#include <iostream>
#include <iomanip>
#include <mutex>
#include <sstream>
#include "URAnalysis/AnalysisFW/interface/Logger.h"
#include <stdio.h> 

class ProgressBar{
public:
  ProgressBar(long int max, unsigned int update=1, bool active=true):
    active_(active),
    mutex_(),
    max_(max),
    update_every_(update),
    counter_(0),
    header_size_(10)
  {
    //FIXME: should get the size of the terminal

    //Yes, a system call. I found no better way than this
    //$COLUMNS is not an environmental variable, so the class 
    //cannot access it. ioctl calls can be very disruptive as
    //they can (and will) change the behavior of the system
    //in a randomic way

    FILE *in = popen("tput cols", "r");
    char buff[100];
    if(!in){
      Logger::log().warning() << "I could not get the " <<
        "Size of your terminal, setting it to 100" << std::endl;
    }
    fgets(buff, sizeof(buff), in);
    wsize_ = atoi(buff);
    pclose(in);

    if(wsize_ > 250){
      Logger::log().warning() << "Your window size looks " <<
	"suspiciously bin (" << wsize_ << " chars)" <<
	"limiting progress bar to 100" << std::endl;
      wsize_ = 100;
    }
    //wsize_ = 100;
    wsize_ -= header_size_;
    //0% update
    this->update(false);
  }

  //inline to be faster
  inline void update(bool increment=true)
  {
    if(!active_) return;
    std::lock_guard<std::mutex> lock(mutex_);
    if(increment) counter_++;
    if(counter_ % update_every_ != 0) return;
    if(counter_ > max_){
      Logger::log().error() << "You are trying to force the prgress " << 
	"of the progressbar to values > 100%! I will ignore it." << std::endl;
      return;
    }
    
    float ratio = counter_/(float)max_;
    int   c     = ratio * wsize_;
    std::stringstream bar;
    std::cerr << setw(3) << (int)(ratio*100) << "% [";
    //std::cerr << c << " " << wsize_;
    for (int x=0; x<c; x++)      std::cerr << "=";
    for (int x=c; x<wsize_; x++) std::cerr << " ";
    std::cerr << "]\r" << std::flush;
    if(c == wsize_) std::cerr << std::endl;
  }  

private:
  bool active_;
  std::mutex mutex_;
  const long int max_; 
  const unsigned int update_every_;
  unsigned int counter_;
  int wsize_;
  const int header_size_;
};

#endif
