#include "URAnalysis/AnalysisFW/interface/EventList.h"
#include "URAnalysis/AnalysisFW/interface/Logger.h"
#include <iostream>
#include <fstream>
#include <algorithm>
using namespace std;

EventList::EventList(std::string filename) {
	ifstream txtfile;
	txtfile.open(filename);
	if(!txtfile.good()) { 
		Logger::log().fatal() << "Cannot open: " << filename << endl;
		throw 42; 
	}
	UInt_t run, lumi, evt;
	char separator;
	while(txtfile >> run >> separator >> lumi >> separator >> evt) {
		evts_.push_back(
			std::make_tuple(run, lumi, evt)
			);
	}
	sort(evts_.begin(), evts_.end());
}

bool EventList::contains(UInt_t run, UInt_t lumi, UInt_t evt) {
	return binary_search(
		evts_.begin(), evts_.end(),
		std::make_tuple(run, lumi, evt)
		);
}
