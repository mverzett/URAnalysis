/** \class PATIpEmbedder
 *
 * Embed the track IP w.r.t an input PV as a ValueMap
 * Also produces the 3D & 2D IP and significance
 *
 * \author Konstantinos A. Petridis, Imperial College;
 *  modified by Christian Veelken
 *  modified by Evan Friis
 *  imported from https://github.com/mverzett/FinalStateAnalysis/blob/master/PatTools/plugins/PATLeptonIpEmbedder.cc
 *  and modified by Mauro Verzetti
 */

#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/EventSetup.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/Framework/interface/EDProducer.h"

#include "URAnalysis/PATTools/interface/PATLeptonTrackVectorExtractor.h"
#include "DataFormats/VertexReco/interface/Vertex.h"
#include "DataFormats/VertexReco/interface/VertexFwd.h"
#include "DataFormats/Common/interface/ValueMap.h"

#include "TrackingTools/TransientTrack/interface/TransientTrack.h"
#include "TrackingTools/TransientTrack/interface/TransientTrackBuilder.h"
#include "TrackingTools/Records/interface/TransientTrackRecord.h"
#include "TrackingTools/IPTools/interface/IPTools.h"

#include <vector>
#include <iostream>

template<typename T>
class PATIpEmbedder : public edm::EDProducer {
public:
  PATIpEmbedder(const edm::ParameterSet& pset);
  virtual ~PATIpEmbedder(){}
  void produce(edm::Event& evt, const edm::EventSetup& es);
private:
  edm::InputTag src_;
  edm::InputTag vtxSrc_;
  ura::PATLeptonTrackVectorExtractor<T> trackExtractor_;
};

template<typename T>
PATIpEmbedder<T>::PATIpEmbedder(const edm::ParameterSet& pset) {
  src_ = pset.getParameter<edm::InputTag>("src");
  vtxSrc_ = pset.getParameter<edm::InputTag>("vtxSrc");
  produces< edm::ValueMap<float> >("ipDXY");
  produces< edm::ValueMap<float> >("dz"	);
  produces< edm::ValueMap<float> >("vz"	);
  produces< edm::ValueMap<float> >("ip3D");
  produces< edm::ValueMap<float> >("ip3DS");
  produces< edm::ValueMap<float> >("missingInnerHits");
  // produces< edm::ValueMap<float> >("tip");
  // produces< edm::ValueMap<float> >("tipS" );
}

template<typename T>
void PATIpEmbedder<T>::produce(edm::Event& evt, const edm::EventSetup& es) {
  edm::Handle<edm::View<T> > handle;
  evt.getByLabel(src_, handle);

  edm::Handle<reco::VertexCollection> vertices;
  evt.getByLabel(vtxSrc_, vertices);

  const reco::Vertex& thePV = *vertices->begin();

  typedef std::pair<bool,Measurement1D> IPResult;

  std::vector< double > v_ip;
  std::vector< double > v_dz;
  std::vector< double > v_vz;
  std::vector< double > v_ip3D;
  std::vector< double > v_ip3DS;
  std::vector< double > v_missingInnerHits;
  // std::vector< double > v_tip;
  // std::vector< double > v_tipS;

  v_ip.reserve(handle->size());
  v_dz.reserve(handle->size());
  v_vz.reserve(handle->size());
  v_ip3D.reserve(handle->size());
  v_ip3DS.reserve(handle->size());
  v_missingInnerHits.reserve(handle->size());
  // v_tip.reserve(handle->size());
  // v_tipS.reserve(handle->size());

  for (size_t iObject = 0; iObject < handle->size(); ++iObject) {
    const T& object = handle->at(iObject);
    std::vector<const reco::Track*> tracks = trackExtractor_(object);
    const reco::Track* track = tracks.size() ? tracks.at(0) : NULL;
    double ip = -999;
    double dz = -999;
    double vz = -999;
    double ip3D = -999;
    double ip3DS = -999;
	double missingInnerHits = -999;
    // double tip = -1;
    // double tipS = -1;

    if (track) {
      ip = track->dxy(thePV.position());
      dz = track->dz(thePV.position());
      vz = track->vz();
      ip3D = fabs(object.dB(T::PV3D));
      ip3DS = fabs(object.edB(T::PV3D));
	  missingInnerHits = track->hitPattern().numberOfLostHits(reco::HitPattern::MISSING_INNER_HITS);
		//std::cout << missingInnerHits << std::endl;
    }

    v_ip.push_back(ip);
    v_dz.push_back(dz);
    v_vz.push_back(vz);
    v_ip3D.push_back(ip3D);
    v_ip3DS.push_back(ip3DS);
	v_missingInnerHits.push_back(missingInnerHits);

    // v_tip.push_back(tip);
    // v_tipS.push_back(tipS);
  }

  std::auto_ptr<edm::ValueMap<float> > vmap_ip(new edm::ValueMap<float>());
  std::auto_ptr<edm::ValueMap<float> > vmap_dz(new edm::ValueMap<float>());
  std::auto_ptr<edm::ValueMap<float> > vmap_vz(new edm::ValueMap<float>());
  std::auto_ptr<edm::ValueMap<float> > vmap_ip3D(new edm::ValueMap<float>());
  std::auto_ptr<edm::ValueMap<float> > vmap_ip3DS(new edm::ValueMap<float>());
  std::auto_ptr<edm::ValueMap<float> > vmap_missingInnerHits(new edm::ValueMap<float>());
  // std::auto_ptr<edm::ValueMap<float> > vmap_tip(new edm::ValueMap<float>());
  // std::auto_ptr<edm::ValueMap<float> > vmap_tipS(new edm::ValueMap<float>());

  edm::ValueMap<float>::Filler filler_ip(*vmap_ip);
  edm::ValueMap<float>::Filler filler_dz(*vmap_dz);
  edm::ValueMap<float>::Filler filler_vz(*vmap_vz);
  edm::ValueMap<float>::Filler filler_ip3D(*vmap_ip3D);
  edm::ValueMap<float>::Filler filler_ip3DS(*vmap_ip3DS);
  edm::ValueMap<float>::Filler filler_missingInnerHits(*vmap_missingInnerHits);
  // edm::ValueMap<float>::Filler filler_tip(*vmap_tip);
  // edm::ValueMap<float>::Filler filler_tipS(*vmap_tipS);

  filler_ip.insert(   handle, v_ip.begin()   , v_ip.end()   );
  filler_dz.insert(   handle, v_dz.begin()   , v_dz.end()   );
  filler_vz.insert(   handle, v_vz.begin()   , v_vz.end()   );
  filler_ip3D.insert( handle, v_ip3D.begin() , v_ip3D.end() );
  filler_ip3DS.insert(handle, v_ip3DS.begin(), v_ip3DS.end());
  filler_missingInnerHits.insert(handle, v_missingInnerHits.begin(), v_missingInnerHits.end());
  // filler_tip.insert(  handle, v_tip.begin()  , v_tip.end()  );
  // filler_tipS.insert( handle, v_tipS.begin() , v_tipS.end() );

  filler_ip.fill();
  filler_dz.fill();
  filler_vz.fill();
  filler_ip3D.fill();
  filler_ip3DS.fill();
  filler_missingInnerHits.fill();
  // filler_tip.fill();
  // filler_tipS.fill();

  evt.put(vmap_ip, "ipDXY");
  evt.put(vmap_dz, "dz" );
  evt.put(vmap_vz, "vz" );
  evt.put(vmap_ip3D, "ip3D");
  evt.put(vmap_ip3DS, "ip3DS");
  evt.put(vmap_missingInnerHits, "missingInnerHits");
  // evt.put(vmap_tip, "tip");
  // evt.put(vmap_tipS, "tipS" );
}

#include "DataFormats/PatCandidates/interface/Electron.h"
#include "DataFormats/PatCandidates/interface/Muon.h"
#include "DataFormats/PatCandidates/interface/Tau.h"

typedef PATIpEmbedder<pat::Muon> PATMuonIpEmbedder;
typedef PATIpEmbedder<pat::Electron> PATElectronIpEmbedder;
//typedef PATIpEmbedder<pat::Tau> PATTauIpEmbedder;

#include "FWCore/Framework/interface/MakerMacros.h"
DEFINE_FWK_MODULE(PATMuonIpEmbedder);
DEFINE_FWK_MODULE(PATElectronIpEmbedder);
//DEFINE_FWK_MODULE(PATTauIpEmbedder);
