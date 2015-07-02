// -*- C++ -*-
//
// Package:    URAnalysis/MetaNtuplizer.cc
// Class:      MetaNtuplizer.cc
// 
/**\class MetaNtuplizer.cc MetaNtuplizer.cc.cc URAnalysis/MetaNtuplizer.cc/plugins/MetaNtuplizer.cc.cc

 Description: Computes and stores in the rootfile the Meta Information needed

*/
//
// Original Author:  Mauro Verzetti
//         Created:  Thu, 20 Nov 2014 11:34:09 GMT
//
//


// system include files
#include <memory>

// user include files
#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/EDAnalyzer.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/LuminosityBlock.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "DataFormats/Provenance/interface/Provenance.h"
#include "DataFormats/Common/interface/MergeableCounter.h"
#include "FWCore/ServiceRegistry/interface/Service.h"
#include "FWCore/ParameterSet/interface/Registry.h"
#include "CommonTools/UtilAlgos/interface/TFileService.h"
#include <DQMServices/Core/interface/DQMStore.h>
#include <DQMServices/Core/interface/MonitorElement.h>
#include "FWCore/ParameterSet/interface/ParameterSetDescription.h"
#include "FWCore/ParameterSet/interface/ConfigurationDescriptions.h"
#include "TTree.h"
#include "TObjString.h"
#include "TH1F.h"

#include <map>
#include <string>
#include <iostream>
#include <sstream> 

//
// class declaration
//

class MetaNtuplizer : public edm::EDAnalyzer {
public:
  explicit MetaNtuplizer(const edm::ParameterSet&);
  ~MetaNtuplizer() {}

  static void fillDescriptions(edm::ConfigurationDescriptions& descriptions);


private:
  virtual void beginJob() override;
  virtual void analyze(const edm::Event&, const edm::EventSetup&) override {}
  virtual void endJob() override;

  virtual void endRun(edm::Run const&, edm::EventSetup const&) override {}
  virtual void endLuminosityBlock(edm::LuminosityBlock const&, edm::EventSetup const&) override;

  // ----------member data ---------------------------
  TTree *meta_tree_;
  std::map<std::string, std::string> to_json_;
  bool string_dumped_, isMC_;
  MonitorElement *pu_distro_;
  unsigned int lumi_;
  unsigned int run_;
  unsigned long long processed_;
};

//
// constants, enums and typedefs
//

//
// static data member definitions
//

//
// constructors and destructor
//
MetaNtuplizer::MetaNtuplizer(const edm::ParameterSet& iConfig):
  string_dumped_(false),
  isMC_(iConfig.getParameter<bool>("isMC"))
{
  //dump direct information
  to_json_.insert(std::make_pair<std::string, std::string>("tuple_commit", iConfig.getParameter<std::string>("commit"))); 
  to_json_.insert(std::make_pair<std::string, std::string>("tuple_user", iConfig.getParameter<std::string>("user"))); 
  to_json_.insert(std::make_pair<std::string, std::string>("tuple_cmsswVersion", iConfig.getParameter<std::string>("cmsswVersion"))); 
  to_json_.insert(std::make_pair<std::string, std::string>("tuple_date", iConfig.getParameter<std::string>("date"))); 
  to_json_.insert(std::make_pair<std::string, std::string>("tuple_globalTag", iConfig.getParameter<std::string>("globalTag")));
}

//
// member functions
//

// ------------ method called once each job just after ending the event loop  ------------
void MetaNtuplizer::beginJob()
{
  edm::Service<TFileService> fs;

  meta_tree_ = fs->make<TTree>( "meta"  , "File Meta Information");
  meta_tree_->Branch("run", &run_);
  meta_tree_->Branch("lumi", &lumi_);
  meta_tree_->Branch("processed", &processed_);
}
 
void MetaNtuplizer::endJob() 
{
  edm::Service<TFileService> fs;
  fs->file().cd();

  if(isMC_){
    //std::cout<< "accessing DQM Store!" << std::endl;
    DQMStore& dqmStore = (*edm::Service<DQMStore>());
    pu_distro_ = dqmStore.get("PUDistribution");
    pu_distro_->getTH1F()->Write();
  }

  std::stringstream stream;
  stream << "{" << std::endl;
  for(auto entry = to_json_.begin(); entry != to_json_.end(); ++entry)
    {
      stream << "   \"" << entry->first << "\" : \"" << entry->second << "\"," << std::endl;
    }
  stream << "}" << std::endl;
  
  fs->make<TObjString>(stream.str().c_str());
}

// ------------ method called when ending the processing of a luminosity block  ------------
void 
MetaNtuplizer::endLuminosityBlock(edm::LuminosityBlock const& block, edm::EventSetup const&)
{
  edm::Handle<edm::MergeableCounter> counter;
  block.getByLabel("processedEvents", counter);

  lumi_ = block.luminosityBlock();
  run_ = block.run();
  processed_ = counter->value;
  meta_tree_->Fill();

  /*if(!string_dumped_)
    {
      string_dumped_ = true;
      const edm::Provenance& prov = block.getProvenance(counter.id());
      
      edm::ParameterSet pset;
      edm::pset::Registry::instance()->getMapped(prov.branchDescription().parameterSetID(), pset);

      to_json_.insert(std::make_pair<std::string, std::string>("pat_commit"      , pset.getParameter<std::string>("commit")));
      to_json_.insert(std::make_pair<std::string, std::string>("pat_user"        , pset.getParameter<std::string>("user")));
      to_json_.insert(std::make_pair<std::string, std::string>("pat_cmsswVersion", pset.getParameter<std::string>("cmsswVersion")));
      to_json_.insert(std::make_pair<std::string, std::string>("pat_date"        , pset.getParameter<std::string>("date")));
      to_json_.insert(std::make_pair<std::string, std::string>("pat_globalTag"   , pset.getParameter<std::string>("globalTag")));
      }*/
}

// ------------ method fills 'descriptions' with the allowed parameters for the module  ------------
void
MetaNtuplizer::fillDescriptions(edm::ConfigurationDescriptions& descriptions) {
  //The following says we do not know what parameters are allowed so do no validation
  // Please change this to state exactly what you do use, even if it is no parameters
  edm::ParameterSetDescription desc;
  desc.setUnknown();
  descriptions.addDefault(desc);
}

//define this as a plug-in
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/PluginManager/interface/ModuleDef.h"
DEFINE_FWK_MODULE(MetaNtuplizer);
