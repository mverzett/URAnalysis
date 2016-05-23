// -*- C++ -*-
//
// Package:    URAnalysis/NtupleLHEParticles.cc
// Class:      NtupleLHEParticles.cc
// 
/**\class NtupleLHEParticles.cc NtupleLHEParticles.cc URAnalysis/NtupleLHEParticles.cc/plugins/NtupleLHEParticles.cc

 Description: Dumps LHE particles into the ntuple content
*/
//
// Original Author:  Mauro Verzetti
//
#include <vector>
#include <string>
#include <iostream>

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

#include "SimDataFormats/GeneratorProducts/interface/LHEEventProduct.h"

class NtupleLHEParticles : public Obj2BranchBase{
public:
  /// default constructor
  NtupleLHEParticles(edm::ParameterSet iConfig);
  /// default destructor
  ~NtupleLHEParticles();

private:
  virtual void analyze(const edm::Event&, const edm::EventSetup&);

  // ----------member data ---------------------------
  bool isMC_;
  edm::InputTag src_;
  edm::EDGetTokenT<LHEEventProduct> srcToken_;
   
  std::vector<float> px_;
  std::vector<float> py_;
  std::vector<float> pz_;
  std::vector<float> e_;
  std::vector<int> pdgid_;
  std::vector<int> status_;
  std::vector<int> fmother_;
  std::vector<int> lmother_;
	int npnlo_;
};

// Constructor
NtupleLHEParticles::NtupleLHEParticles(edm::ParameterSet iConfig): 
	Obj2BranchBase(iConfig),
	src_(iConfig.getParameter<edm::InputTag>("src")),
	srcToken_(consumes<LHEEventProduct>(src_))
{
  // By having this class inherit from Obj2BranchBAse, we have access to our tree_, no need for TFileService
  // Book branches:
  tree_.branch(prefix_+SEPARATOR+"px", &px_); 
  tree_.branch(prefix_+SEPARATOR+"py", &py_); 
  tree_.branch(prefix_+SEPARATOR+"pz", &pz_); 
  tree_.branch(prefix_+SEPARATOR+"e", &e_); 
  tree_.branch(prefix_+SEPARATOR+"pdgid", &pdgid_); 
  tree_.branch(prefix_+SEPARATOR+"status", &status_); 
  tree_.branch(prefix_+SEPARATOR+"fmother", &fmother_); 
  tree_.branch(prefix_+SEPARATOR+"lmother", &lmother_); 
}

// Destructor
NtupleLHEParticles::~NtupleLHEParticles()
{
}

void NtupleLHEParticles::analyze(const edm::Event& iEvent, const edm::EventSetup& iSetup)
{
	px_.clear();
	py_.clear();
	pz_.clear();
	e_.clear();
	pdgid_.clear();
	status_.clear();
	fmother_.clear();
	lmother_.clear();

	edm::Handle<LHEEventProduct> lheinfo;
	iEvent.getByToken(srcToken_, lheinfo);
	if(lheinfo.isValid())
	{
		const lhef::HEPEUP& hepeup = lheinfo->hepeup();
		for(size_t p = 0 ; p < hepeup.IDUP.size() ; ++p)
		{
			const lhef::HEPEUP::FiveVector& mom = hepeup.PUP[p];
			px_.push_back(mom[0]);
			py_.push_back(mom[1]);
			pz_.push_back(mom[2]);
			e_.push_back(mom[3]);
			pdgid_.push_back(hepeup.IDUP[p]);
			status_.push_back(hepeup.ISTUP[p]);
			fmother_.push_back(hepeup.MOTHUP[p].first);
			lmother_.push_back(hepeup.MOTHUP[p].second);
		}	
	} 
}

#include "FWCore/Framework/interface/MakerMacros.h"
DEFINE_FWK_MODULE(NtupleLHEParticles);
