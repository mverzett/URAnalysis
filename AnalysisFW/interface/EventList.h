#ifndef EventList_h
#define EventList_h

#include <tuple>  
#include <vector>  
#include <string>
#include "Rtypes.h"

class EventList {
public:
	EventList(std::string filename); //parses input file
	EventList(): evts_(){}
	bool contains(UInt_t run, UInt_t lumi, UInt_t evt);
	bool active() {return (evts_.size() > 0);}
private:
	std::vector< std::tuple<UInt_t, UInt_t, UInt_t> > evts_;
};

#endif
