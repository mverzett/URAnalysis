// -*- C++ -*-
//
// Package:    URAnalysis/NtupleFilter.cc
// Class:      NtupleFilter.cc
// 
/**\class NtupleFilter.cc NtupleFilter.cc.cc URAnalysis/NtupleFilter.cc/plugins/NtupleFilter.cc.cc

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
#include <regex>

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


#include "DataFormats/Common/interface/TriggerResults.h"
#include "DataFormats/PatCandidates/interface/PackedTriggerPrescales.h"

using namespace std;

class NtupleFilter : public Obj2BranchBase{
	public:
		/// default constructor
		NtupleFilter(edm::ParameterSet iConfig);
		/// default destructor
		~NtupleFilter();

	private:
		virtual void analyze(const edm::Event&, const edm::EventSetup&);

		// ----------member data ---------------------------
		bool isMC_;
		vector<string> triggerSelection_;
		uint32_t currentrun;
		edm::EDGetTokenT<edm::TriggerResults> srcTokenRECO;
		edm::EDGetTokenT<edm::TriggerResults> srcTokenPAT;

		vector<int> selectedBits;
		vector<int> results;
		//int HBHE;

};

// Constructor
NtupleFilter::NtupleFilter(edm::ParameterSet iConfig): 
	Obj2BranchBase(iConfig),
	triggerSelection_(iConfig.getParameter<vector<string> >("filterSelection")),
	currentrun(0)
{
    srcTokenRECO = consumes<edm::TriggerResults>(edm::InputTag("TriggerResults", "" , "RECO"));	
    srcTokenPAT = consumes<edm::TriggerResults>(edm::InputTag("TriggerResults", "" , "PAT"));

	results.resize(triggerSelection_.size());
	selectedBits.resize(triggerSelection_.size());
	for(size_t t = 0 ; t < triggerSelection_.size() ; ++t)
	{
		tree_.branch(prefix_+SEPARATOR+triggerSelection_[t], &(results[t]), (prefix_+SEPARATOR+triggerSelection_[t]+"/I").c_str()); 
	}
	//tree_.branch(prefix_+SEPARATOR+"HBHEnew", &HBHE, (prefix_+SEPARATOR+"HBHEnew/I").c_str()); 
}

// Destructor
NtupleFilter::~NtupleFilter()
{
}

void NtupleFilter::analyze(const edm::Event& iEvent, const edm::EventSetup& iSetup)
{

	edm::Handle<edm::TriggerResults> triggerBits;
	//edm::Handle<pat::PackedTriggerPrescales> triggerPrescales;
	//edm::Handle<bool> hbheres;
	//iEvent.getByLabel(edm::InputTag("HBHENoiseFilterResultProducer", "HBHENoiseFilterResult"), hbheres);

	//HBHE = (*hbheres) ? 1 : -1;

	//iEvent.getByLabel(triggerBits_, triggerBits);
	iEvent.getByToken(srcTokenPAT, triggerBits);
	if(!triggerBits.isValid())
	{
		iEvent.getByToken(srcTokenRECO, triggerBits);
	}

	if(iEvent.id().run() != currentrun)
	{
		currentrun = iEvent.id().run();
		const edm::TriggerNames& names = iEvent.triggerNames(*triggerBits);
		for(size_t tr = 0 ; tr < triggerSelection_.size() ; ++tr)
		{
			selectedBits[tr] = 0;
			for(size_t tn = 0 ; tn < triggerBits->size() ; ++tn)
			{
	cout << names.triggerName(tn) << " " << tn << endl;
				if(names.triggerName(tn).find(triggerSelection_[tr]) != string::npos)
				{
					selectedBits[tr] = tn;
					break;
				}
			}
		}				
	}

	for(size_t i = 0 ; i < selectedBits.size() ; ++i)
	{
		//cout << i << " " << selectedBits[i] << " " << triggerBits->accept(selectedBits[i]) << endl;
		if(selectedBits[i] == 0)
		{
			results[i] = 0;
			continue;
		}
		if(triggerBits->accept(selectedBits[i]))
		{
			results[i] = 1; 
		}
		else
		{
			results[i] = -1; 
		}
	}
}

#include "FWCore/Framework/interface/MakerMacros.h"
DEFINE_FWK_MODULE(NtupleFilter);
