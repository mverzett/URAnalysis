/*
class: NtupleDoubleProducer

EDAnalyzer that produces information on a single double stored 
in the event content and stores them in an URNtuple.

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

class NtupleDoubleProducer: public Obj2BranchBase{
public:
  NtupleDoubleProducer(edm::ParameterSet cfg);
  ~NtupleDoubleProducer(){}

private:
  virtual void analyze(const edm::Event&, const edm::EventSetup&);
  virtual void debug(){}

  edm::InputTag src_;
  double value_;
};

NtupleDoubleProducer::NtupleDoubleProducer(edm::ParameterSet cfg):
  Obj2BranchBase(cfg),
  src_(cfg.getParameter<edm::InputTag>("src"))
{
  tree_.branch(prefix_+SEPARATOR+"value", &value_, "value/D"); 
}

void NtupleDoubleProducer::analyze(const edm::Event& evt, const edm::EventSetup&)
{
  //
  edm::Handle< double > handle;
  evt.getByLabel(src_, handle);
  value_ = *handle;
  //std::cout << "Filling with " << value_ << std::end
}


//define CMSSW plug-ins
DEFINE_FWK_MODULE(NtupleDoubleProducer);





