// -*- C++ -*-
//
// Package:    WeightedEventCountProducer
// Class:      WeightedEventCountProducer
// 
/**\class WeightedEventCountProducer WeightedEventCountProducer.cc CommonTools/UtilAlgos/plugins/WeightedEventCountProducer.cc

Description: An event counter that can store the weighted number of events in the lumi block 

*/


// system include files
#include <memory>
#include <vector>
#include <algorithm>
#include <iostream>

// user include files
#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/one/EDProducer.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/LuminosityBlock.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"

#include "DataFormats/Common/interface/MergeableCounter.h"
#include "SimDataFormats/GeneratorProducts/interface/LHEEventProduct.h"

class WeightedEventCountProducer : public edm::one::EDProducer<edm::one::WatchLuminosityBlocks,
                                                       edm::EndLuminosityBlockProducer> {
public:
  explicit WeightedEventCountProducer(const edm::ParameterSet&);
  ~WeightedEventCountProducer();

private:
  virtual void produce(edm::Event &, const edm::EventSetup&) override;
  virtual void beginLuminosityBlock(const edm::LuminosityBlock &, const edm::EventSetup&) override;
  virtual void endLuminosityBlock(edm::LuminosityBlock const&, const edm::EventSetup&) override;
  virtual void endLuminosityBlockProduce(edm::LuminosityBlock &, const edm::EventSetup&) override;
      
  // ----------member data ---------------------------

  long long int weightedEventsProcessedInLumi_;
  edm::InputTag lhes_;

};



using namespace edm;
using namespace std;



WeightedEventCountProducer::WeightedEventCountProducer(const edm::ParameterSet& iConfig):
    lhes_(iConfig.getParameter<edm::InputTag>("lhes"))
{
  produces<edm::MergeableCounter, edm::InLumi>();
}


WeightedEventCountProducer::~WeightedEventCountProducer(){}


void
WeightedEventCountProducer::produce(edm::Event& iEvent, const edm::EventSetup& iSetup){
  edm::Handle<LHEEventProduct > lhes;
  iEvent.getByLabel(lhes_, lhes);
  float w = lhes->hepeup().XWGTUP;
  short sign = (w > 0) ? 1 : ((w < 0) ? -1 : 0);
  weightedEventsProcessedInLumi_+=sign;
  return;
}


void 
WeightedEventCountProducer::beginLuminosityBlock(const LuminosityBlock & theLuminosityBlock, const EventSetup & theSetup) {
  weightedEventsProcessedInLumi_ = 0;
  return;
}

void 
WeightedEventCountProducer::endLuminosityBlock(LuminosityBlock const& theLuminosityBlock, const EventSetup & theSetup) {
}

void 
WeightedEventCountProducer::endLuminosityBlockProduce(LuminosityBlock & theLuminosityBlock, const EventSetup & theSetup) {
  LogTrace("EventCounting") << "endLumi: adding " << weightedEventsProcessedInLumi_ << " events" << endl;

  auto_ptr<edm::MergeableCounter> numEventsPtr(new edm::MergeableCounter);
  numEventsPtr->value = weightedEventsProcessedInLumi_;
  theLuminosityBlock.put(numEventsPtr);

  return;
}



//define this as a plug-in
DEFINE_FWK_MODULE(WeightedEventCountProducer);