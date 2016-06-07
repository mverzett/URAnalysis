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
#include "DataFormats/PatCandidates/interface/Electron.h"
#include "DataFormats/METReco/interface/PFMET.h"

using namespace std;

class NtupleMETUncertainty : public Obj2BranchBase{
public:
  /// default constructor
  NtupleMETUncertainty(edm::ParameterSet iConfig);
  /// default destructor
  ~NtupleMETUncertainty();

private:
  virtual void analyze(const edm::Event&, const edm::EventSetup&);
	void dumpNormal(const pat::MET&);
	void dumpUserCands(const pat::MET&);

  // ----------member data ---------------------------
  edm::InputTag src_;
	bool useUserCands_;
  bool isMC_;
  edm::EDGetTokenT<vector<pat::MET> > srcToken_;
  
	vector<float> metpx;
	vector<float> metpy;
	vector<float> metpxsmear;
	vector<float> metpysmear;
	vector<float> metxunc;
	vector<float> metyunc;
	vector<float> metxuncjes;
	vector<float> metyuncjes;
	vector<float> metxuncjer;
	vector<float> metyuncjer;

};

// Constructor
NtupleMETUncertainty::NtupleMETUncertainty(edm::ParameterSet iConfig): 
	Obj2BranchBase(iConfig),
	src_(iConfig.getParameter<edm::InputTag>("src")),
	useUserCands_(iConfig.getParameter<bool>("useUserCands")),
	isMC_(iConfig.getParameter<bool>("isMC"))
{
  srcToken_ = consumes<vector<pat::MET> >(src_);
  // By having this class inherit from Obj2BranchBAse, we have access to our tree_, no need for TFileService
  // Book branches:
  tree_.branch(prefix_+SEPARATOR+"px", &metpx); 
  tree_.branch(prefix_+SEPARATOR+"py", &metpy); 
	tree_.branch(prefix_+SEPARATOR+"pxsmear", &metpxsmear);
	tree_.branch(prefix_+SEPARATOR+"pysmear", &metpysmear);
  tree_.branch(prefix_+SEPARATOR+"pxunc", &metxunc); 
  tree_.branch(prefix_+SEPARATOR+"pyunc", &metyunc); 
  tree_.branch(prefix_+SEPARATOR+"pxuncJES", &metxuncjes); 
  tree_.branch(prefix_+SEPARATOR+"pyuncJES", &metyuncjes); 
  tree_.branch(prefix_+SEPARATOR+"pxuncJER", &metxuncjer); 
  tree_.branch(prefix_+SEPARATOR+"pyuncJER", &metyuncjer); 
}

// Destructor
NtupleMETUncertainty::~NtupleMETUncertainty()
{
}

void NtupleMETUncertainty::dumpNormal(const pat::MET& met) {
	//metpx.push_back(met.shiftedPx(pat::MET::NoShift));	
	//metpy.push_back(met.shiftedPy(pat::MET::NoShift));	
	//this SHOULD be the smeared one
	metpx.push_back(met.px());	
	metpy.push_back(met.py());	
	//Threfore we put the same value twice
	metpxsmear.push_back(met.px());
	metpysmear.push_back(met.py());
	
	cout << "Accessing lepton shit" << endl;
	float _metxunc = pow(met.shiftedPx(pat::MET::MuonEnUp) - met.shiftedPx(pat::MET::MuonEnDown), 2);
	_metxunc += pow(met.shiftedPx(pat::MET::ElectronEnUp) - met.shiftedPx(pat::MET::ElectronEnDown), 2);
	_metxunc += pow(met.shiftedPx(pat::MET::TauEnUp) - met.shiftedPx(pat::MET::TauEnDown), 2);
	_metxunc += pow(met.shiftedPx(pat::MET::UnclusteredEnUp) - met.shiftedPx(pat::MET::UnclusteredEnDown), 2);
	metxunc.push_back(sqrt(_metxunc)/2.);
	
	cout << "Accessing JES shit" << endl;
	float _metxuncjet = pow(met.shiftedPx(pat::MET::JetEnUp) - met.shiftedPx(pat::MET::JetEnDown), 2);
	metxuncjes.push_back(sqrt(_metxuncjet)/2.);
	
	cout << "Accessing JER shit" << endl;
	_metxuncjet = pow(met.shiftedPx(pat::MET::JetResUp) - met.shiftedPx(pat::MET::JetResDown), 2);
	metxuncjer.push_back(sqrt(_metxuncjet)/2.);
	
	float _metyunc = pow(met.shiftedPy(pat::MET::MuonEnUp) - met.shiftedPy(pat::MET::MuonEnDown), 2);
	_metyunc += pow(met.shiftedPy(pat::MET::ElectronEnUp) - met.shiftedPy(pat::MET::ElectronEnDown), 2);
	_metyunc += pow(met.shiftedPy(pat::MET::TauEnUp) - met.shiftedPy(pat::MET::TauEnDown), 2);
	_metyunc += pow(met.shiftedPy(pat::MET::UnclusteredEnUp) - met.shiftedPy(pat::MET::UnclusteredEnDown), 2);
	metyunc.push_back(sqrt(_metyunc)/2.);
	
	float _metyuncjet = pow(met.shiftedPy(pat::MET::JetEnUp) - met.shiftedPy(pat::MET::JetEnDown), 2);
	metyuncjes.push_back(sqrt(_metyuncjet)/2.);
	
	_metyuncjet = pow(met.shiftedPy(pat::MET::JetResUp) - met.shiftedPy(pat::MET::JetResDown), 2);
	metyuncjer.push_back(sqrt(_metyuncjet)/2.);
}

void NtupleMETUncertainty::dumpUserCands(const pat::MET& met) {
	metpx.push_back(met.px());	
	metpy.push_back(met.py());	
	
	//Access smeared
	if(isMC_) {
		if(!met.hasUserCand("JER")) throw cms::Exception("Runtime") << "MET object has no 'JER' user cand\n";
		metpxsmear.push_back(met.userCand("JER")->px());
		metpysmear.push_back(met.userCand("JER")->py());		
	}
	else {
		metpxsmear.push_back(met.px());
		metpysmear.push_back(met.py());
	}

	//access original to get leptons/unclustered systematics
	if(isMC_) {
		if(!met.hasUserCand("ORIGINAL")) throw cms::Exception("Runtime") << "MET object has no 'ORIGINAL' user cand\n"; 
		//cast fom candidatePtr to pat::MET
		pat::MET const *original = dynamic_cast<pat::MET const *>( met.userCand("ORIGINAL").get() );
		
		if(!original) throw cms::Exception("Runtime") << "Could not cast 'ORIGINAL' user cand to pat::MET type\n";
		float _metxunc = pow(original->shiftedPx(pat::MET::MuonEnUp) - original->shiftedPx(pat::MET::MuonEnDown), 2);
		_metxunc += pow(original->shiftedPx(pat::MET::ElectronEnUp) - original->shiftedPx(pat::MET::ElectronEnDown), 2);
		_metxunc += pow(original->shiftedPx(pat::MET::TauEnUp) - original->shiftedPx(pat::MET::TauEnDown), 2);
		_metxunc += pow(original->shiftedPx(pat::MET::UnclusteredEnUp) - original->shiftedPx(pat::MET::UnclusteredEnDown), 2);
		metxunc.push_back(sqrt(_metxunc)/2.);

		float _metyunc = pow(original->shiftedPy(pat::MET::MuonEnUp) - original->shiftedPy(pat::MET::MuonEnDown), 2);
		_metyunc += pow(original->shiftedPy(pat::MET::ElectronEnUp) - original->shiftedPy(pat::MET::ElectronEnDown), 2);
		_metyunc += pow(original->shiftedPy(pat::MET::TauEnUp) - original->shiftedPy(pat::MET::TauEnDown), 2);
		_metyunc += pow(original->shiftedPy(pat::MET::UnclusteredEnUp) - original->shiftedPy(pat::MET::UnclusteredEnDown), 2);
		metyunc.push_back(sqrt(_metyunc)/2.);
	}
	else { //for data pad with zeros
		metxunc.push_back(0.);
		metyunc.push_back(0.);
	}

	//access JES uncertainties
	if(isMC_) {
		if(!met.hasUserCand("JES+") || !met.hasUserCand("JES-")) throw cms::Exception("Runtime") << "MET object has no 'JES+' or 'JES-' user cands\n";
		metxuncjes.push_back(abs(met.userCand("JES+")->px() - met.userCand("JES-")->px())/2.);
		metyuncjes.push_back(abs(met.userCand("JES+")->py() - met.userCand("JES-")->py())/2.);
	} 
	else {
		metxuncjes.push_back(0.);
		metyuncjes.push_back(0.);
	}

	//access JER uncertainties 
	if(isMC_) {
		if(!met.hasUserCand("JER+") || !met.hasUserCand("JER-")) throw cms::Exception("Runtime") << "MET object has no 'JER+' or 'JER-' user cands\n";
		metxuncjer.push_back(abs(met.userCand("JER+")->px() - met.userCand("JER-")->px())/2.);
		metyuncjer.push_back(abs(met.userCand("JER+")->py() - met.userCand("JER-")->py())/2.);		
	}
	else {
		metxuncjer.push_back(0.);
		metyuncjer.push_back(0.);
	}
}

void NtupleMETUncertainty::analyze(const edm::Event& iEvent, const edm::EventSetup& iSetup)
{
	metpx.clear();
	metpy.clear();
	metpxsmear.clear();
	metpysmear.clear();
	metxunc.clear();
	metyunc.clear();
	metxuncjes.clear();
	metyuncjes.clear();
	metxuncjer.clear();
	metyuncjer.clear();
	edm::Handle<vector<pat::MET>> hmet;
	iEvent.getByToken(srcToken_, hmet);

	const vector<pat::MET>& met = *hmet;

	for(size_t n = 0 ; n < met.size() ; ++n) {
		if(useUserCands_) {
			dumpUserCands(met[n]);			
		}
		else {
			dumpNormal(met[n]);
		}
	}
}

#include "FWCore/Framework/interface/MakerMacros.h"
DEFINE_FWK_MODULE(NtupleMETUncertainty);
