// -*- C++ -*-
//
// Package:    URAnalysis/NtupleGenParticleInheritance.cc
// Class:      NtupleGenParticleInheritance.cc
// 
/**\class NtupleGenParticleInheritance.cc NtupleGenParticleInheritance.cc.cc URAnalysis/NtupleGenParticleInheritance.cc/plugins/NtupleGenParticleInheritance.cc.cc

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

class NtupleGenParticleInheritance : public Obj2BranchBase{
public:
  /// default constructor
  NtupleGenParticleInheritance(edm::ParameterSet iConfig);
  /// default destructor
  ~NtupleGenParticleInheritance();

private:
  virtual void analyze(const edm::Event&, const edm::EventSetup&);
  virtual void clear(){index.clear(); 
   		       mom_index.clear(); 
                       num_daughters.clear();
		       first_daughter_index.clear();}

  // ----------member data ---------------------------
  bool isMC_;
  edm::InputTag src_;
  edm::EDGetTokenT<reco::CandidateView> srcToken_;
   
  std::vector<int> index;     // Basically what is the position of this particle in the collection
  std::vector< std::vector<int> > mom_index; // The mother's position in the same collection
  // It turns out we can have two mothers or more, so we need to make this a vector of vectors 
  std::vector<int> num_daughters; // How many daughter particles this particle has
  std::vector<int> first_daughter_index; // The index of the first daughter (the assumption here is that all the daughters are listed consecutively after the first.
};

// Constructor
NtupleGenParticleInheritance::NtupleGenParticleInheritance(edm::ParameterSet iConfig): 
	Obj2BranchBase(iConfig),
	src_(iConfig.getParameter<edm::InputTag>("src")),
        srcToken_(consumes<reco::CandidateView>(src_))	
{
  // By having this class inherit from Obj2BranchBAse, we have access to our tree_, no need for TFileService
  // Book branches:
  tree_.branch(prefix_+SEPARATOR+"idx", &index);
  tree_.branch(prefix_+SEPARATOR+"momIdx", &mom_index); 
  tree_.branch(prefix_+SEPARATOR+"nDaught", &num_daughters);           // we don't really need these two branches
  tree_.branch(prefix_+SEPARATOR+"firstDaughtIdx", &first_daughter_index); // since all the info is available for the mothers
}

// Destructor
NtupleGenParticleInheritance::~NtupleGenParticleInheritance()
{
}

void
NtupleGenParticleInheritance::analyze(const edm::Event& iEvent, const edm::EventSetup& iSetup)
{
  //before all, clear the vectors for this event:
  clear();
  
  edm::Handle<reco::CandidateView> GenParticles;
  iEvent.getByToken(srcToken_, GenParticles);
	if(!GenParticles.isValid()) return;
  
  // We need to make a first pass to be able to find the mothers later:
  std::vector<const reco::Candidate *> cands;
  std::vector<const reco::Candidate *>::const_iterator found = cands.begin();
  for(reco::CandidateView::const_iterator p = GenParticles->begin(); p != GenParticles->end(); ++ p) {
      cands.push_back(&*p);
  }
  
  int idx = -1; // the index for all particles
  int iDa1 = -1; // the index of the first daughter
  for(reco::CandidateView::const_iterator p  = GenParticles->begin(); p != GenParticles->end(); p ++) {
     // Particle Index
     idx =  p - GenParticles->begin();
     
     // There can be more than one mother:
     std::vector<int> thisparticle_mothers_index;
     thisparticle_mothers_index.clear();
     int nMo = p->numberOfMothers();
     //std::cout << " idx = " << idx << " nMo = " << nMo << " mom_idx = " ;
     int nDa = p->numberOfDaughters();
     // Find the indeces for the mothers and fill a per-particle-vector:
     for (int m=0; m<nMo; m++){
	int im=-1;
     	found = find(cands.begin(), cands.end(), p->mother(m));
     	if(found != cands.end()) im = found - cands.begin();
	thisparticle_mothers_index.push_back(im);
     }
     //std::copy(thisparticle_mothers_index.begin(), thisparticle_mothers_index.end(), std::ostream_iterator<int>(std::cout, ",")); std::cout << std::endl;

     // Find the index for the first daughter: 
     found = find(cands.begin(), cands.end(), p->daughter(0));
     if(found != cands.end()) iDa1 = found - cands.begin();
     
     // Now add all the values for this GenParticle to the vectors that will become branches:
     index.push_back(idx);
     mom_index.push_back(thisparticle_mothers_index); // this is a vector of vectors
     num_daughters.push_back(nDa);
     first_daughter_index.push_back(iDa1);
   }

   // Once we are out of the loop over particles, there is no need to explicitly fill the branches.
   // The vectors are filled and they will be assigned to the branches by the TreeFiller at the end of the event. 
  
//    std::cout << "-------Inheritance---------" << std::endl;
//    for ( const std::vector<int> &v : mom_index ){
//         std::cout << "[";
//    	for ( int x : v ) std::cout << x << ' ';
//    		std::cout << "],";
//    }
//    std::cout << std::endl;

//   std::copy(mom_index.begin(), mom_index.end(), std::ostream_iterator<int>(std::cout, ","));
//   std::cout << std::endl;
//   std::copy(num_daughters.begin(), num_daughters.end(), std::ostream_iterator<int>(std::cout, ","));
//   std::cout << std::endl;
  
}

#include "FWCore/Framework/interface/MakerMacros.h"
DEFINE_FWK_MODULE(NtupleGenParticleInheritance);
