#include "CutFlowTracker.h"
#include "TH1F.h"
#include "Logger.h"

void CutFlowTracker::track(std::string pointname)
{
	if(!active_) return;
  if(verbose_) Logger::log().debug() << pointname << std::endl;
  float to_add = (weight_) ? *weight_ : 1.;
	auto point = cutflow_.find(pointname);
	if(point != cutflow_.end()){
		point->second.second += to_add;
	}
	else {
		cutflow_.insert( 
			std::make_pair(
				pointname,
				std::make_pair(
					npoints_,
					to_add
					)
				)
			);
		npoints_++;
	}
}

void CutFlowTracker::writeTo(TFile &file)
{
	file.cd();
	TH1F histo("cut_flow", "cut_flow", npoints_, 0, npoints_);
	TAxis *xax = histo.GetXaxis();
	for(auto& point : cutflow_){
		xax->SetBinLabel(point.second.first+1, point.first.c_str());
		histo.SetBinContent(point.second.first+1, point.second.second);
	}
	histo.Write();
}
