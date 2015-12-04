/*
class: NtupleCollectionProducer<EDObject>

EDAnalyzer that produces information on a EDCollection 
(vector of EDObjects) and stores them in an URNtuple.

The variable computation and branch filling is outsourced
to VObjBranchExpr, while this class takes care of branch 
bookkeeping and enforces consistency between different 
branches, i.e. different variables pertaining to the same 
object are stored in the same vector position in the 
respective branches.

Template specialization and consequent CMSSW plug-in
definition at the end of the file. 

Author: Mauro Verzetti (UR)
 */


// system include files
#include <memory>

// user include files
#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/EDAnalyzer.h"

#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"

#include "URAnalysis/Ntuplizer/interface/Obj2BranchBase.h"
#include "URAnalysis/Ntuplizer/interface/VObjBranchExpr.h"
#include "FWCore/Utilities/interface/InputTag.h"
#include <vector>
#include <string>
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "DataFormats/Common/interface/Handle.h"
#include "TTree.h"
#include "FWCore/Framework/interface/Event.h"
#include <iostream>

template <class EDObject>
class NtupleCollectionProducer: public Obj2BranchBase{
public:
  NtupleCollectionProducer(edm::ParameterSet cfg);
  ~NtupleCollectionProducer(){ for(size_t i=0; i<branches_.size(); i++) delete branches_[i]; }

private:
  virtual void analyze(const edm::Event&, const edm::EventSetup&);
  virtual void clear(){for(auto&& branch : branches_) branch->clear();}
  virtual void debug(){for(auto&& branch : branches_) branch->debug();}

  edm::InputTag src_;
  std::vector< ObjExpression<EDObject>* > branches_;
};

template <class EDObject>
NtupleCollectionProducer<EDObject>::NtupleCollectionProducer(edm::ParameterSet cfg):
  Obj2BranchBase(cfg),
  src_(cfg.getParameter<edm::InputTag>("src"))
{
  std::vector< edm::ParameterSet > branches = cfg.getParameter<std::vector< edm::ParameterSet > >("branches");
  branches_.reserve(branches.size());
  for(auto&& branch : branches)
    {
      BranchInfo info(prefix_, branch);
      try
	{
	  branches_.push_back(VObjBranchExprFactory<EDObject>(info, tree_));
	}
      catch(cms::Exception& iException)
	{
	  iException << "Caught exception in building branch: "
		     << info.name << " with formula: " << info.expr;
	  throw;
	}
    }
}

template <class EDObject>
void NtupleCollectionProducer<EDObject>::analyze(const edm::Event& evt, const edm::EventSetup&)
{
  //before all, clear the vectors
  clear();

  //
  edm::Handle< std::vector<EDObject> > handle;
  evt.getByLabel(src_, handle);

  if(!handle.isValid()) return;

  size_t size = handle->size();
  //std::cout << "got " << src_ << " with size: " << size << std::endl;
  for(auto&& branch : branches_)
    {
      branch->reserve(size);
    }

  //std::cout << "reserved space" << std::endl;
  for(auto&& obj : *handle)
    {
      for(auto&& branch : branches_)
	{
	  branch->fill(obj);
	}
    }
  //std::cout << "filled branches" << std::endl;
}

//PAT Includes                                                                                                                                                                                                                              
#include "DataFormats/PatCandidates/interface/Electron.h"
#include "DataFormats/PatCandidates/interface/Muon.h"
#include "DataFormats/PatCandidates/interface/MET.h"
#include "DataFormats/PatCandidates/interface/Jet.h"
#include "DataFormats/PatCandidates/interface/Photon.h"
#include "DataFormats/VertexReco/interface/Vertex.h"
#include "SimDataFormats/PileupSummaryInfo/interface/PileupSummaryInfo.h"
#include "DataFormats/HepMCCandidate/interface/GenParticle.h"
#include "DataFormats/JetReco/interface/GenJet.h"

//CMSSW does not like templates, so use typedefs
typedef NtupleCollectionProducer<pat::Muon> NtupleMuonsProducer;
typedef NtupleCollectionProducer<pat::Electron> NtupleElectronsProducer;
typedef NtupleCollectionProducer<pat::MET> NtupleMETProducer;
typedef NtupleCollectionProducer<pat::Jet> NtupleJetsProducer;
typedef NtupleCollectionProducer<pat::Photon> NtuplePhotonsProducer;
typedef NtupleCollectionProducer<reco::Vertex> NtupleVerticesProducer; 
typedef NtupleCollectionProducer<PileupSummaryInfo> NtuplePUInfoProducer; 
typedef NtupleCollectionProducer<reco::GenParticle> NtupleGenParticlesProducer; 
typedef NtupleCollectionProducer<reco::GenJet> NtupleGenJetsProducer; 

//define CMSSW plug-ins
DEFINE_FWK_MODULE(NtupleMuonsProducer);
DEFINE_FWK_MODULE(NtupleElectronsProducer);
DEFINE_FWK_MODULE(NtupleMETProducer);
DEFINE_FWK_MODULE(NtupleJetsProducer);
DEFINE_FWK_MODULE(NtuplePhotonsProducer);
DEFINE_FWK_MODULE(NtupleVerticesProducer);
DEFINE_FWK_MODULE(NtuplePUInfoProducer);
DEFINE_FWK_MODULE(NtupleGenParticlesProducer);
DEFINE_FWK_MODULE(NtupleGenJetsProducer);



