/*
class NtupleJetTracksProducer:

produces vactor<vector<floats> > containing information about the charged PF Candidates inside a Jet

Author: Mauro Verzetti
 */

#include "FWCore/Framework/interface/EDAnalyzer.h"
#include "URAnalysis/Ntuplizer/interface/Obj2BranchBase.h"

#include <vector>
#include <string>
#include <limits> //numeric_limits

#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Utilities/interface/InputTag.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/ServiceRegistry/interface/Service.h"
#include "Math/VectorUtil.h"
#include "DataFormats/Math/interface/deltaR.h"
#include "URAnalysis/Ntuplizer/interface/ObjExpression.h" //defines the separator                                                                                                                               
#include "DataFormats/PatCandidates/interface/Jet.h"
#include "DataFormats/PatCandidates/interface/PackedCandidate.h"
#include "TMath.h"
#include <math.h>
#include <iostream>

class NtupleJetTracksProducer : public Obj2BranchBase{
public:
  /// default constructor
  NtupleJetTracksProducer(edm::ParameterSet iConfig);
  /// default destructor
  ~NtupleJetTracksProducer() {}

private:
  virtual void analyze(const edm::Event&, const edm::EventSetup&);
  virtual void clear(){
    trk_max_pt_.clear(); 
    trk_min_pt_.clear(); 
    trk_rms_pt_.clear();     
    trk_rms_dr_.clear(); 
  }

  // ----------member data ---------------------------
  edm::InputTag src_;
  edm::EDGetTokenT< std::vector<pat::Jet> > srcToken_;

  std::vector< float > trk_max_pt_; 
  std::vector< float > trk_min_pt_; 
  std::vector< float > trk_rms_pt_; 
  std::vector< float > trk_avg_pt_; 

  std::vector< float > trk_rms_dr_; 

  // std::vector< std::vector<float> > trk_pt_; // tracks pts
  // std::vector< std::vector<float> > trk_eta_; // tracks pts
  // std::vector< std::vector<float> > trk_phi_; // tracks pts

};

// Constructor
NtupleJetTracksProducer::NtupleJetTracksProducer(edm::ParameterSet iConfig): 
	Obj2BranchBase(iConfig),
	src_(iConfig.getParameter<edm::InputTag>("src")),
  srcToken_(consumes< std::vector<pat::Jet> >(src_))	
{
  // By having this class inherit from Obj2BranchBAse, we have access to our tree_, no need for TFileService
  // Book branches:
  tree_.branch(prefix_+SEPARATOR+"TrkMaxPt", &trk_max_pt_);
  tree_.branch(prefix_+SEPARATOR+"TrkMinPt", &trk_min_pt_);
  tree_.branch(prefix_+SEPARATOR+"TrkAvgPt", &trk_avg_pt_);
  tree_.branch(prefix_+SEPARATOR+"TrkRmsPt", &trk_rms_pt_);
  tree_.branch(prefix_+SEPARATOR+"TrkRmsDr", &trk_rms_dr_);
}

void
NtupleJetTracksProducer::analyze(const edm::Event& iEvent, const edm::EventSetup& iSetup)
{
  //before all, clear the vectors for this event:
  clear();
  
  edm::Handle< std::vector<pat::Jet> > jets_handle;
  iEvent.getByToken(srcToken_, jets_handle);
  const std::vector<pat::Jet> *jets = jets_handle.product();

  //loop over the jets
  for(auto& jet : *(jets)) {
    float pt_sum=0;
    float pt_sqSum = 0;
    float pt_min = std::numeric_limits<float>::max();
    float pt_max = 0.;
    float dr_sqSum = 0;
    size_t n_constituents = jet.numberOfDaughters();
    for(size_t idx=0; idx < n_constituents; ++idx) {
      const reco::Candidate* component = jet.daughter(idx);
      if(component && component->charge() != 0) { //PF Candidates may also be neutral!
        double pt = component->pt();
        pt_sum += pt;
        pt_sqSum += std::pow(pt, 2);
        double dr = reco::deltaR(*component, jet);
        dr_sqSum += std::pow(dr, 2);
        if(pt < pt_min) pt_min = pt;
        if(pt > pt_max) pt_max = pt;
      }
    }
     
    trk_max_pt_.push_back(pt_max);
    trk_min_pt_.push_back(pt_min);
    trk_avg_pt_.push_back(pt_sum/n_constituents);
    trk_rms_pt_.push_back(TMath::Sqrt(pt_sqSum/n_constituents));
    trk_rms_dr_.push_back(TMath::Sqrt(dr_sqSum/n_constituents));
  }
}

#include "FWCore/Framework/interface/MakerMacros.h"
DEFINE_FWK_MODULE(NtupleJetTracksProducer);
