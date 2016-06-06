#ifndef Worker_h
#define Worker_h

#include <thread>
#include <string>

/*
Simple generic implementation of a thread worker
 */

class Worker{
public:
  Worker(std::string &id):
    thread_(),
    id_(id)
	{}

  void start(){thread_ = std::thread(&Worker::work, this);}
  void join(){thread_.join();}
	std::string id() {return id_;}
	virtual void start_nothread(){work();}
  virtual ~Worker() {}

private:
  virtual void work() = 0;
  std::thread thread_;

protected:
  std::string id_;
};

#endif
