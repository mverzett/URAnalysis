// -*- C++ -*-
//
// Package:    URAnalysis/NtupleMETUncertainty.cc
// Class:      NtupleMETUncertainty.cc
// 
/**\class NtupleMETUncertainty.cc NtupleMETUncertainty.cc.cc URAnalysis/NtupleMETUncertainty.cc/plugins/NtupleMETUncertainty.cc.cc

 Description: Add inheritance information to GenParticles and store it in the URTree.
              The inheritance information (mom_index) consists in assigning an integer counter to each 
	      GenParticle in the input collection that points to its mother.

 Useful to take a look at these pages, (I stole the bulk of the code from the second link):
 https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookGenParticleCandidate
 https://cmssdt.cern.ch/SDT/lxr/source/PhysicsTools/HepMCCandAlgos/plugins/ParticleListDrawer.cc
*/
//
// Original Author:  Aran Garcia-Bellido
//         Created:  Wed, 22 Jan 2015 15:08:09 GMT
//
#include <vector>
#include <string>
#include <iostream>
#include <cmath>

#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/EDAnalyzer.h"
#include "FWCore/Utilities/interface/InputTag.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/ServiceRegistry/interface/Service.h"
#include "Math/VectorUtil.h"
#include "DataFormats/HepMCCandidate/interface/GenParticle.h"
#include "DataFormats/Candidate/interface/Candidate.h"
#include "DataFormats/Candidate/interface/CandidateFwd.h"
#include "DataFormats/Common/interface/Ref.h"
#include "URAnalysis/Ntuplizer/interface/Obj2BranchBase.h"
#include "URAnalysis/Ntuplizer/interface/ObjExpression.h" //defines the separator

#include "DataFormats/PatCandidates/interface/MET.h"

using namespace std;

class NtupleMETUncertainty : public Obj2BranchBase{
public:
  /// default constructor
  NtupleMETUncertainty(edm::ParameterSet iConfig);
  /// default destructor
  ~NtupleMETUncertainty();

private:
  virtual void analyze(const edm::Event&, const edm::EventSetup&);

  // ----------member data ---------------------------
  bool isMC_;
  edm::InputTag src_;
   
	vector<float> metpx;
	vector<float> metpy;
	vector<float> metxunc;
	vector<float> metyunc;
	vector<float> metxuncjet;
	vector<float> metyuncjet;
};

// Constructor
NtupleMETUncertainty::NtupleMETUncertainty(edm::ParameterSet iConfig): 
	Obj2BranchBase(iConfig),
	src_(iConfig.getParameter<edm::InputTag>("src"))
{
  // By having this class inherit from Obj2BranchBAse, we have access to our tree_, no need for TFileService
  // Book branches:
  tree_.branch(prefix_+SEPARATOR+"px", &metpx); 
  tree_.branch(prefix_+SEPARATOR+"py", &metpy); 
  tree_.branch(prefix_+SEPARATOR+"pxunc", &metxunc); 
  tree_.branch(prefix_+SEPARATOR+"pyunc", &metyunc); 
  tree_.branch(prefix_+SEPARATOR+"pxuncjet", &metxuncjet); 
  tree_.branch(prefix_+SEPARATOR+"pyuncjet", &metyuncjet); 
}

// Destructor
NtupleMETUncertainty::~NtupleMETUncertainty()
{
}

void NtupleMETUncertainty::analyze(const edm::Event& iEvent, const edm::EventSetup& iSetup)
{
	metpx.clear();
	metpy.clear();
	metxunc.clear();
	metyunc.clear();
	metxuncjet.clear();
	metyuncjet.clear();
	edm::Handle<vector<pat::MET>> hmet;
	iEvent.getByLabel(src_, hmet);

	const vector<pat::MET>& met = *hmet;

	for(size_t n = 0 ; n < met.size() ; ++n)
	{
		//metpx.push_back(met[n].shiftedPx(pat::MET::NoShift));	
		//metpy.push_back(met[n].shiftedPy(pat::MET::NoShift));	
		metpx.push_back(met[n].px());	
		metpy.push_back(met[n].py());	
	
		float _metxunc = pow(met[n].shiftedPx(pat::MET::MuonEnUp) - met[n].shiftedPx(pat::MET::MuonEnDown), 2);
		_metxunc += pow(met[n].shiftedPx(pat::MET::ElectronEnUp) - met[n].shiftedPx(pat::MET::ElectronEnDown), 2);
		_metxunc += pow(met[n].shiftedPx(pat::MET::TauEnUp) - met[n].shiftedPx(pat::MET::TauEnDown), 2);
		_metxunc += pow(met[n].shiftedPx(pat::MET::UnclusteredEnUp) - met[n].shiftedPx(pat::MET::UnclusteredEnDown), 2);
		metxunc.push_back(sqrt(_metxunc)/2.);

		float _metxuncjet = pow(met[n].shiftedPx(pat::MET::JetEnUp) - met[n].shiftedPx(pat::MET::JetEnDown), 2);
		_metxuncjet += pow(met[n].shiftedPx(pat::MET::JetResUp) - met[n].shiftedPx(pat::MET::JetResDown), 2);
		metxuncjet.push_back(sqrt(_metxuncjet)/2.);

		float _metyunc = pow(met[n].shiftedPy(pat::MET::MuonEnUp) - met[n].shiftedPy(pat::MET::MuonEnDown), 2);
		_metyunc += pow(met[n].shiftedPy(pat::MET::ElectronEnUp) - met[n].shiftedPy(pat::MET::ElectronEnDown), 2);
		_metyunc += pow(met[n].shiftedPy(pat::MET::TauEnUp) - met[n].shiftedPy(pat::MET::TauEnDown), 2);
		_metyunc += pow(met[n].shiftedPy(pat::MET::UnclusteredEnUp) - met[n].shiftedPy(pat::MET::UnclusteredEnDown), 2);
		metyunc.push_back(sqrt(_metyunc)/2.);

		float _metyuncjet = pow(met[n].shiftedPy(pat::MET::JetEnUp) - met[n].shiftedPy(pat::MET::JetEnDown), 2);
		_metyuncjet += pow(met[n].shiftedPy(pat::MET::JetResUp) - met[n].shiftedPy(pat::MET::JetResDown), 2);
		metyuncjet.push_back(sqrt(_metyuncjet)/2.);

	}
}

#include "FWCore/Framework/interface/MakerMacros.h"
DEFINE_FWK_MODULE(NtupleMETUncertainty);
