#include "PUReweighter.h"
#include "TH1.h"
#include "TFile.h"
#include "Logger.h"
#include "DataFile.h"
#include "TMath.h"

void PUReweighter::init(std::string sample_fname, std::string data_fname, std::string hdata, std::string hmc) {
  TFile mc_file( DataFile(sample_fname).path().c_str() );
  TFile data_file( DataFile(data_fname).path().c_str() );
  TH1 *data_h = (TH1*) data_file.Get(hdata.c_str());
  if(!data_h) {Logger::log().error() << "Data PU histogram ("<< hdata <<") not found!" << std::endl; throw 42;}
  TH1 *mc_h = (TH1*) mc_file.Get(hmc.c_str());
  if(!mc_h) {Logger::log().error() << "MC PU histogram ("<< mc_h <<") not found!" << std::endl; throw 42;}

	//Normalize, to be sure
  if(data_h->Integral() > 0) data_h->Scale(1./data_h->Integral());
  else {Logger::log().error() << "The data PU histogram has null or negative integral!" << std::endl; throw 42;}

	if(mc_h->Integral() > 0) mc_h->Scale(1./mc_h->Integral());
  else {Logger::log().error() << "The data PU histogram has null or negative integral!" << std::endl; throw 42;}

  int min_bins = TMath::Min(data_h->GetNbinsX(), mc_h->GetNbinsX());

	for(int ibin=1; ibin<=min_bins; ++ibin){
    //check for bin consistency
    if(data_h->GetXaxis()->GetBinCenter(ibin) != mc_h->GetXaxis()->GetBinCenter(ibin) ||
       data_h->GetXaxis()->GetBinWidth(ibin) != mc_h->GetXaxis()->GetBinWidth(ibin) ) {
      Logger::log().error() << "The data and MC PU histogram have inconsistent binning at bin "<< ibin <<"!" << std::endl;
      throw 42;
    }

		float mc_cont = mc_h->GetBinContent(ibin);
		float w = (mc_cont != 0) ? data_h->GetBinContent(ibin)/mc_cont : 0.;
		weights_.push_back(w);
	}	
	wsize_=weights_.size();
}
