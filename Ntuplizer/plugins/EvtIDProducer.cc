// system include files
#include <memory>

// user include files
#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/EDAnalyzer.h"

#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"

#include "URAnalysis/Ntuplizer/interface/Obj2BranchBase.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "TTree.h"
#include <iostream>

/*
class: EvtIDProducer

Simple, hard-coded EDAnalyzer that produces eventID information (run, lumi and 
event number) and puts in the URNtuple

Author: Mauro Verzetti
 */

class EvtIDProducer: public Obj2BranchBase{
public:
  EvtIDProducer(edm::ParameterSet cfg);
  ~EvtIDProducer(){}

private:
  virtual void analyze(const edm::Event&, const edm::EventSetup&);
  unsigned int lumi_;
  unsigned int run_;
  unsigned long long evt_;
};

EvtIDProducer::EvtIDProducer(edm::ParameterSet cfg):
  Obj2BranchBase(cfg)
{
  //book fixed branches
  tree_.branch("run", &run_, "run/i");
  tree_.branch("lumi", &lumi_, "lumi/i");
  tree_.branch("evt", &evt_, "evt/i");
}

void EvtIDProducer::analyze(const edm::Event& evt, const edm::EventSetup&)
{
  lumi_= evt.id().luminosityBlock();
  run_ = evt.id().run();
  evt_ = evt.id().event();
}

//define CMSSW plug-ins
DEFINE_FWK_MODULE(EvtIDProducer);



