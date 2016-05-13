#ifndef URGenericMuonsSelector_h
#define URGenericMuonsSelector_h



#include "URAnalysis/AnalysisFW/interface/URSelector.h"



template<typename Object, const std::vector< Object >& (URStreamer::*Collection)() >
class URGenericMuonsSelector: public URSelector
{
  public:
    URGenericMuonsSelector(const std::string name) : URSelector(name)
    {
      initialize();
    }

    virtual bool select(URStreamer& event)
    {
      int nMuons = 0;
      selectedMuonCollection_.clear();
      for(auto muon = (event.*Collection)().begin(); muon != (event.*Collection)().end(); muon++)
      {
        if(select(*muon))
        {
          selectedMuonCollection_.push_back(&(*muon));
          nMuons++;
        }
      }
      if(nMuons >= minNMuons_)
        return true;
      return false;
    }
    
    bool select(const Object& muon)
    {
      if(muon.Pt() > muonPtMin_ &&
        fabs(muon.Eta()) < muonEtaMax_)
      {
        return (this->*muonSelection_)(muon);
      }
      return false;
    }
    
    std::vector< const Object* > getSelectedMuons()
    {
      return selectedMuonCollection_;
    }

      
    void configure() override
    {
      URSelector::configure();
      if(!isConfigured_)
      {    
        addCfgParameter<double>("muonPtMin", "Minimum pt threshold of muon selection.");
        addCfgParameter<double>("muonEtaMax", "Maximum eta threshold of muon selection.");
        addCfgParameter<int>("minNMuons", "Minimum number of good muons required per event.");
        addCfgParameter<std::string>("muonSelectionName", "Name of muon selection to apply.");
        
        registerConfiguration();
        
        muonPtMin_ = getCfgParameter<double>("muonPtMin");
        muonEtaMax_ = getCfgParameter<double>("muonEtaMax");
        minNMuons_ = getCfgParameter<int>("minNMuons");
        muonSelectionName_ = getCfgParameter<std::string>("muonSelectionName");
        
        setMuonSelection();
        
        isConfigured_ = true;
      }
    }
    
    typedef bool (URGenericMuonsSelector<Object, Collection>::*muonSelection)(const Object&); 
    
  private:
    void initialize()
    {
      isConfigured_ = false;
      muonPtMin_ = 0;
      muonEtaMax_ = 0;
      minNMuons_ = 999;
      selectedMuonCollection_.clear();
      configure();
    }
    
    bool tightMuonSelection(const Object& muon)
    {
      return (muon.isGlobal() && muon.isTracker() && muon.validHits()>2);
    }
    
    bool looseMuonSelection(const Object& muon)
    {
      return(muon.isGlobal() && muon.isTracker());
    }
    
    bool passThroughMuonSelection(const Object& muon)
    {
      Logger::log().warning() << "W A R N I N G ! URGenericMuonsSelector: using pass-through muon selection! Please set correct selection type in cfg file!\n";
      return true;
    }
    
    void setMuonSelection()
    {
      if(!muonSelectionName_.compare("tight"))
        muonSelection_ = &URGenericMuonsSelector<Object, Collection>::tightMuonSelection;
      else if(!muonSelectionName_.compare("loose"))
        muonSelection_ = &URGenericMuonsSelector<Object, collection>::looseMuonSelection;
      else
        muonSelection_ = &URGenericMuonsSelector<Object, Collection>::passThroughMuonSelection;
    }
    
    bool isConfigured_;
    double muonPtMin_;
    double muonEtaMax_;
    int minNMuons_;
    std::string muonSelectionName_;
    muonSelection muonSelection_;
    std::vector< const Object* > selectedMuonCollection_;
};



#endif // URGenericMuonsSelector_h
