/*
Embeds trigger matching information into PAT candidates,
can be easily extended to embed any sort of ValueMap
 */


// system include files
#include <memory>

// user include files
#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/EDProducer.h"

#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"

#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/Utilities/interface/InputTag.h"
#include "DataFormats/Common/interface/Handle.h"
#include "DataFormats/PatCandidates/interface/TriggerObjectStandAlone.h"
#include "DataFormats/Common/interface/RefToBase.h"

#include <vector>
#include <string>
//
// class declaration
//

template<typename PATObject>
class PATEmbedder : public edm::EDProducer {
public:
  explicit PATEmbedder(const edm::ParameterSet&);
  ~PATEmbedder();

  static void fillDescriptions(edm::ConfigurationDescriptions& descriptions);

private:
  virtual void beginJob() override;
  virtual void produce(edm::Event&, const edm::EventSetup&) override;
  virtual void endJob() override;
      
  //virtual void beginRun(edm::Run const&, edm::EventSetup const&) override;
  //virtual void endRun(edm::Run const&, edm::EventSetup const&) override;
  //virtual void beginLuminosityBlock(edm::LuminosityBlock const&, edm::EventSetup const&) override;
  //virtual void endLuminosityBlock(edm::LuminosityBlock const&, edm::EventSetup const&) override;
  typedef std::vector<edm::InputTag> vInputTag;
  typedef std::vector<std::string> vstring;
  typedef std::vector<PATObject> collection;
  // ----------member data ---------------------------
  
  edm::InputTag src_;
  edm::EDGetTokenT< collection > srcToken_;
  vInputTag float_maps_;
  std::vector< edm::EDGetTokenT< edm::ValueMap<float> > > float_mapTokens_;
  vstring ufloat_names_;
  //vInputTag int_maps_;
  vInputTag trig_matches_;
  std::vector< edm::EDGetTokenT< edm::Association<pat::TriggerObjectStandAloneCollection> > > trig_matchTokens_;
  vstring tring_paths_;
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
template<typename PATObject>
PATEmbedder<PATObject>::PATEmbedder(const edm::ParameterSet& cfg):
	src_(cfg.getParameter<edm::InputTag>("src")),
	srcToken_(consumes< collection >(src_)),
	//float_maps_(cfg.getParameter<vInputTag>("floatMaps")),
	//int_maps_(cfg.getParameter<vInputTag>("intMaps")),
	trig_matches_(cfg.getParameter<vInputTag>("trigMatches")),
	tring_paths_(cfg.getParameter<vstring>("trigPaths"))
{
	edm::ParameterSet float_maps = cfg.getParameter<edm::ParameterSet>("floatMaps");
	ufloat_names_ = float_maps.getParameterNames();
	for(auto&& tag : trig_matches_)
	{
std::cout << "TRIG: " << tag << std::endl;
		trig_matchTokens_.push_back(consumes< edm::Association<pat::TriggerObjectStandAloneCollection> >(tag));
	}

	for(auto&& name : ufloat_names_){
std::cout << "USER: " << name << std::endl;
		float_maps_.push_back(float_maps.getParameter<edm::InputTag>(name));
		float_mapTokens_.push_back(consumes< edm::ValueMap<float> >(float_maps_.back()));
	}

	produces<collection>();
}


template<typename PATObject>
PATEmbedder<PATObject>::~PATEmbedder()
{
 
   // do anything here that needs to be done at desctruction time
   // (e.g. close files, deallocate resources etc.)

}


//
// member functions
//

// ------------ method called to produce the data  ------------
template<typename PATObject>
void
PATEmbedder<PATObject>::produce(edm::Event& iEvent, const edm::EventSetup& iSetup)
{
  edm::Handle< collection > handle;
  iEvent.getByToken(srcToken_, handle);

  //get all trigger matches handles
  std::vector< edm::Handle< edm::Association<pat::TriggerObjectStandAloneCollection> > > match_maps;
  for(auto&& match : trig_matchTokens_){
    edm::Handle< edm::Association<pat::TriggerObjectStandAloneCollection> > i;
    iEvent.getByToken(match, i);
    match_maps.push_back(i);
  }

  //get all user float handles
  std::vector< edm::Handle< edm::ValueMap<float> > > float_maps;
  for(auto&& token : float_mapTokens_){
    edm::Handle< edm::ValueMap<float> > i;
    iEvent.getByToken(token, i);
    float_maps.push_back(i);
  }

  //make new collection 
  std::unique_ptr<collection> output(new collection());

  //loop over the object
  for(size_t idx = 0; idx < handle->size(); idx++){
    PATObject new_cand(handle->at(idx));
    edm::Ref<collection> cand_ref(handle, idx);
    //protection from multiple entries of the same trig object
    //as in https://github.com/cms-sw/cmssw/blob/CMSSW_7_2_X/PhysicsTools/PatAlgos/plugins/PATTriggerMatchEmbedder.cc#L98
    //std::set< TriggerObjectStandAloneRef > cachedRefs; 
    auto path_it = tring_paths_.cbegin();
    for(auto map_it = match_maps.cbegin(); map_it != match_maps.cend(); ++map_it, ++path_it){
      const pat::TriggerObjectStandAloneRef trigRef( (**map_it)[cand_ref] );
      int trig_match = (int) (trigRef.isNonnull() && trigRef.isAvailable());
      new_cand.addUserInt(*path_it, trig_match);
    }

    auto name_it = ufloat_names_.cbegin();
    for(auto map_it = float_maps.cbegin(); map_it != float_maps.cend(); ++map_it, ++name_it){
      float value = (**map_it)[cand_ref];
      new_cand.addUserFloat(*name_it, value);
    }

    //put new candidate
    output->push_back(new_cand);
  }

  iEvent.put(std::move(output)); 
}

// ------------ method called once each job just before starting event loop  ------------
template<typename PATObject>
void 
PATEmbedder<PATObject>::beginJob()
{
}

// ------------ method called once each job just after ending the event loop  ------------
template<typename PATObject>
void 
PATEmbedder<PATObject>::endJob() {
}

// ------------ method called when starting to processes a run  ------------
/*
void
PATEmbedder<PATObject>::beginRun(edm::Run const&, edm::EventSetup const&)
{
}
*/
 
// ------------ method called when ending the processing of a run  ------------
/*
void
PATEmbedder<PATObject>::endRun(edm::Run const&, edm::EventSetup const&)
{
}
*/
 
// ------------ method called when starting to processes a luminosity block  ------------
/*
void
PATEmbedder<PATObject>::beginLuminosityBlock(edm::LuminosityBlock const&, edm::EventSetup const&)
{
}
*/
 
// ------------ method called when ending the processing of a luminosity block  ------------
/*
void
PATEmbedder<PATObject>::endLuminosityBlock(edm::LuminosityBlock const&, edm::EventSetup const&)
{
}
*/
 
// ------------ method fills 'descriptions' with the allowed parameters for the module  ------------
template<typename PATObject>
void
PATEmbedder<PATObject>::fillDescriptions(edm::ConfigurationDescriptions& descriptions) {
  //The following says we do not know what parameters are allowed so do no validation
  // Please change this to state exactly what you do use, even if it is no parameters
  edm::ParameterSetDescription desc;
  desc.setUnknown();
  descriptions.addDefault(desc);
}

#include "DataFormats/PatCandidates/interface/Electron.h"
#include "DataFormats/PatCandidates/interface/Muon.h"
#include "DataFormats/PatCandidates/interface/MET.h"
#include "DataFormats/PatCandidates/interface/Jet.h"
#include "DataFormats/PatCandidates/interface/Photon.h"

//CMSSW does not like templates, so use typedefs
typedef PATEmbedder<pat::Muon> PATMuonsEmbedder;
typedef PATEmbedder<pat::Electron> PATElectronsEmbedder;
typedef PATEmbedder<pat::MET> PATMETEmbedder;
typedef PATEmbedder<pat::Jet> PATJetsEmbedder;
typedef PATEmbedder<pat::Photon> PATPhotonsEmbedder;

//define CMSSW plug-ins
DEFINE_FWK_MODULE(PATMuonsEmbedder);
DEFINE_FWK_MODULE(PATElectronsEmbedder);
DEFINE_FWK_MODULE(PATMETEmbedder);
DEFINE_FWK_MODULE(PATJetsEmbedder);
DEFINE_FWK_MODULE(PATPhotonsEmbedder);
