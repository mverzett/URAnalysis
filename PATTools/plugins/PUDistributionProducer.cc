// -*- C++ -*-
//
// Package:    URAnalysis/PATTools
// Class:      PUDistributionProducer 
//
/* *\class PUDistributionProducer PUDistributionProducer.cc
// 
// Author Mauro Verzetti UR
// Produces the input PU distribution histogram as DQM monitor element,
// can be put in edm Files
*/

#include "FWCore/Framework/interface/EDAnalyzer.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/Utilities/interface/InputTag.h"

// Include DQM core
#include <DQMServices/Core/interface/DQMStore.h>
#include <DQMServices/Core/interface/MonitorElement.h>
#include <DQMServices/Core/interface/DQMEDAnalyzer.h>

//PU Info
#include "SimDataFormats/PileupSummaryInfo/interface/PileupSummaryInfo.h"

// class declaration
class PUDistributionProducer : public DQMEDAnalyzer{

public:
  struct hinfo{
    int nbins;
    double min;
    double max;
    hinfo(int n, double m, double M){
      nbins = n;
      min = m;
      max = M;
    }
    hinfo(const edm::ParameterSet& config){
      nbins = config.getParameter<int>("nbins");
      min = config.getParameter<double>("min");
      max = config.getParameter<double>("max");
    }
  };

  explicit PUDistributionProducer(const edm::ParameterSet& cfg):
    binning_( cfg.getParameter<edm::ParameterSet>("binning") ),
    src_( cfg.getParameter<edm::InputTag>("src") )
  {}
  ~PUDistributionProducer(){}

  virtual void bookHistograms(DQMStore::IBooker &, edm::Run const &, edm::EventSetup const &);
  virtual void dqmBeginRun(const edm::Run&, const edm::EventSetup&) {}
  virtual void analyze(const edm::Event& iEvent, const edm::EventSetup& iSetup);

private:
  MonitorElement* pu_distribution_;
  hinfo binning_;
  edm::InputTag src_;
};

void PUDistributionProducer::bookHistograms(DQMStore::IBooker & ibooker, edm::Run const & iRun, edm::EventSetup const & iSetup)
{
  pu_distribution_ = ibooker.book1D("PUDistribution", "PUDistribution", binning_.nbins, binning_.min, binning_.max);
}

void PUDistributionProducer::analyze(const edm::Event& iEvent, const edm::EventSetup& iSetup)
{
  edm::Handle< std::vector<PileupSummaryInfo> > pu_info;
  iEvent.getByLabel(src_, pu_info);

  //from https://twiki.cern.ch/twiki/bin/view/CMS/PileupMCReweightingUtilities#Calling_the_Function_to_get_an_E
  for(std::vector<PileupSummaryInfo>::const_iterator PVI = pu_info->begin(); PVI != pu_info->end(); ++PVI) 
    {
    int BX = PVI->getBunchCrossing();
    if(BX == 0) 
      { 
        pu_distribution_->Fill( PVI->getTrueNumInteractions() );
        break;
      }
    }
}

#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/PluginManager/interface/ModuleDef.h"
DEFINE_FWK_MODULE(PUDistributionProducer);
