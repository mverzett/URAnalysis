#ifndef URGenericJetsSelector_h
#define URGenericJetsSelector_h



#include "URAnalysis/AnalysisFW/interface/URSelector.h"



template<typename Object, const std::vector< Object >& (URStreamer::*Collection)() >
class URGenericJetsSelector: public URSelector
{
  public:
    URGenericJetsSelector(const std::string name) : URSelector(name)
    {
      initialize();
    }

    virtual bool select(URStreamer& event)
    {
      int nJets = 0;
      selectedJetCollection_.clear();
      for(auto jet = (event.*Collection)().begin(); jet != (event.*Collection)().end(); jet++)
      {
        if(select(*jet))
        {
          selectedJetCollection_.push_back(&(*jet));
          nJets++;
        }
      }
      if(nJets >= minNJets_)
        return true;
      return false;
    }
    
    bool select(const Object& jet)
    {
      if(jet.Pt() > jetPtMin_ &&
        fabs(jet.Eta()) < jetEtaMax_)
      {
        return (this->*jetSelection_)(jet);
      }
      return false;
    }
    
    std::vector< const Object* > getSelectedJets()
    {
      return selectedJetCollection_;
    }

      
    void configure() override
    {
      URSelector::configure();
      if(!isConfigured_)
      {    
        addCfgParameter<double>("jetPtMin", "Minimum pt threshold of jet selection.");
        addCfgParameter<double>("jetEtaMax", "Maximum eta threshold of jet selection.");
        addCfgParameter<int>("minNJets", "Minimum number of good jets required per event.");
        addCfgParameter<std::string>("jetSelectionName", "Name of jet selection to apply.");
        
        registerConfiguration();
        
        jetPtMin_ = getCfgParameter<double>("jetPtMin");
        jetEtaMax_ = getCfgParameter<double>("jetEtaMax");
        minNJets_ = getCfgParameter<int>("minNJets");
        jetSelectionName_ = getCfgParameter<std::string>("jetSelectionName");
        
        setJetSelection();
        
        isConfigured_ = true;
      }
    }
    
    typedef bool (URGenericJetsSelector<Object, Collection>::*jetSelection)(const Object&); 
    
  private:
    void initialize()
    {
      isConfigured_ = false;
      jetPtMin_ = 0;
      jetEtaMax_ = 0;
      minNJets_ = 999;
      selectedJetCollection_.clear();
      configure();
    }
    
    bool tightJetSelection(const Object& jet)
    {
      return true;
    }
    
    bool passThroughJetSelection(const Object& jet)
    {
      Logger::log().warning() << "W A R N I N G ! URGenericJetsSelector: using pass-through jet selection! Please set correct selection type in cfg file!\n";
      return true;
    }
    
    void setJetSelection()
    {
      if(!jetSelectionName_.compare("tight"))
        jetSelection_ = &URGenericJetsSelector<Object, Collection>::tightJetSelection;
      else
        jetSelection_ = &URGenericJetsSelector<Object, Collection>::passThroughJetSelection;
    }
    
    bool isConfigured_;
    double jetPtMin_;
    double jetEtaMax_;
    int minNJets_;
    std::string jetSelectionName_;
    jetSelection jetSelection_;
    std::vector< const Object* > selectedJetCollection_;
};



#endif // URGenericJetsSelector_h
