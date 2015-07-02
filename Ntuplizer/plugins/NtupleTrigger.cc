// -*- C++ -*-
//
// Package:    URAnalysis/NtupleTrigger.cc
// Class:      NtupleTrigger.cc
// 
/**\class NtupleTrigger.cc NtupleTrigger.cc.cc URAnalysis/NtupleTrigger.cc/plugins/NtupleTrigger.cc.cc

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

class NtupleTrigger : public Obj2BranchBase{
	public:
		/// default constructor
		NtupleTrigger(edm::ParameterSet iConfig);
		/// default destructor
		~NtupleTrigger();

	private:
		virtual void analyze(const edm::Event&, const edm::EventSetup&);

		// ----------member data ---------------------------
		bool isMC_;
		edm::InputTag triggerBits_;
		edm::InputTag triggerPrescales_;
		vector<string> triggerSelection_;
		uint32_t currentrun;

		vector<int> selectedBits;
		vector<int> results;

};

// Constructor
NtupleTrigger::NtupleTrigger(edm::ParameterSet iConfig): 
	Obj2BranchBase(iConfig),
	triggerBits_(iConfig.getParameter<edm::InputTag>("trigger")),
	triggerPrescales_(iConfig.getParameter<edm::InputTag>("prescales")),
	triggerSelection_(iConfig.getParameter<vector<string> >("triggerSelection")),
	currentrun(0)
{
	results.resize(triggerSelection_.size());
	selectedBits.resize(triggerSelection_.size());
	for(size_t t = 0 ; t < triggerSelection_.size() ; ++t)
	{
		tree_.branch(prefix_+SEPARATOR+triggerSelection_[t], &(results[t]), (prefix_+SEPARATOR+triggerSelection_[t]+"/I").c_str()); 
	}
}

// Destructor
NtupleTrigger::~NtupleTrigger()
{
}

void NtupleTrigger::analyze(const edm::Event& iEvent, const edm::EventSetup& iSetup)
{

	edm::Handle<edm::TriggerResults> triggerBits;
	edm::Handle<pat::PackedTriggerPrescales> triggerPrescales;

	iEvent.getByLabel(triggerBits_, triggerBits);
	iEvent.getByLabel(triggerPrescales_, triggerPrescales);

	if(iEvent.id().run() != currentrun)
	{
		currentrun = iEvent.id().run();
		const edm::TriggerNames& names = iEvent.triggerNames(*triggerBits);
		for(size_t tr = 0 ; tr < triggerSelection_.size() ; ++tr)
		{
			selectedBits[tr] = 0;
			for(size_t tn = 0 ; tn < triggerBits->size() ; ++tn)
			{
				if(names.triggerName(tn).find(triggerSelection_[tr]+"_v") != string::npos)
				{
					selectedBits[tr] = tn;
					//cout << names.triggerName(tn) << " " << tn << endl;
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
			results[i] = triggerPrescales->getPrescaleForIndex(i); 
		}
		else
		{
			results[i] = triggerPrescales->getPrescaleForIndex(i)*-1; 
		}
	}
}

#include "FWCore/Framework/interface/MakerMacros.h"
DEFINE_FWK_MODULE(NtupleTrigger);
