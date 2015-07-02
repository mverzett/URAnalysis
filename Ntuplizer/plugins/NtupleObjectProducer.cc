/*
class: NtupleObjectProducer<EDObject>

EDAnalyzer that produces information on a single EDObject 
and stores them in an URNtuple.

The variable computation and branch filling is outsourced
to ObjBranchExpr, while this class takes care of branch 
bookkeeping.

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
#include "URAnalysis/Ntuplizer/interface/ObjBranchExpr.h"
#include "FWCore/Utilities/interface/InputTag.h"
#include <vector>
#include <string>
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "DataFormats/Common/interface/Handle.h"
#include "TTree.h"
#include "FWCore/Framework/interface/Event.h"
#include <iostream>

template <class EDObject>
class NtupleObjectProducer: public Obj2BranchBase{
public:
  NtupleObjectProducer(edm::ParameterSet cfg);
  ~NtupleObjectProducer(){ for(size_t i=0; i<branches_.size(); i++) delete branches_[i]; }

private:
  virtual void analyze(const edm::Event&, const edm::EventSetup&);
  virtual void debug(){for(auto&& branch : branches_) branch->debug();}

  edm::InputTag src_;
  std::vector< ObjExpression<EDObject>* > branches_;
};

template <class EDObject>
NtupleObjectProducer<EDObject>::NtupleObjectProducer(edm::ParameterSet cfg):
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
	  branches_.push_back(ObjBranchExprFactory<EDObject>(info, tree_));
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
void NtupleObjectProducer<EDObject>::analyze(const edm::Event& evt, const edm::EventSetup&)
{
  //
  edm::Handle< EDObject > handle;
  evt.getByLabel(src_, handle);

  for(auto&& branch : branches_)
    {
      branch->fill(*handle);
    }
  //std::cout << "filled branches" << std::endl;
}

//PAT Includes                                                                                                                                               
#include "SimDataFormats/GeneratorProducts/interface/GenEventInfoProduct.h"
#include "DataFormats/BeamSpot/interface/BeamSpot.h"

//CMSSW does not like templates, so use typedefs
typedef NtupleObjectProducer<GenEventInfoProduct> NtupleGenInfoProducer;
typedef NtupleObjectProducer<reco::BeamSpot> NtupleBeamSpotProducer;

//define CMSSW plug-ins
DEFINE_FWK_MODULE(NtupleGenInfoProducer);
DEFINE_FWK_MODULE(NtupleBeamSpotProducer);




