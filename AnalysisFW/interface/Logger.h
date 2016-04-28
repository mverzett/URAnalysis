#ifndef Logger_h
#define Logger_h

/*
  class Logger:
  Singleton to handle logging within c++ commands
  in a python-like way
 */
#include <ostream>
#include <sstream>
#include <iostream>

class Messenger {
public:
  Messenger(bool active):
    message_(),
    active_(active) {}
  //No need to implement those
  Messenger(Messenger const&);
  void operator=(Messenger const&);

  ~Messenger()
  {
    if(active_) std::cerr << message_.str();
  }

  template<typename T>
  Messenger& operator<<(T const & t) 
  {
    if(active_) message_ << t;
    return *this;
  }

  Messenger& operator<<(std::ostream&(*f)(std::ostream&))  
  { 
    if(active_) message_ << f; 
    return *this; 
  }
  Messenger& operator<<(std::ios_base&(*f)(std::ios_base&))  
  { 
    if(active_) message_ << f; 
    return *this; 
  }     

private:
  std::stringstream message_; 
  bool active_;
};

class Logger
{
public:
  enum Level{DEBUG, INFO, WARNING, ERROR, FATAL, DISABLED};
  void setLevel(Level lv) {level_ = lv;}
  static Logger& log()
  {
    static Logger val;
    return val;
  }
  
  //void dbg(Level lv) {std::cout << "level " << level_ << ", required: " << lv << std::endl;}
  Messenger debug()  {Messenger m(level_ <= DEBUG)  ; return m;}
  Messenger info()   {Messenger m(level_ <= INFO)   ; return m;}
  Messenger warning(){Messenger m(level_ <= WARNING); return m;}
  Messenger error()  {Messenger m(level_ <= ERROR)  ; return m;}
  Messenger fatal()  {Messenger m(level_ <= FATAL)  ; return m;}

private:
  Logger():
    level_(DISABLED)
  {}
  
  //No need to implement those
  Logger(Logger const&);
  void operator=(Logger const&);

  Level level_;
  //std::ostream null_;
};

#endif
