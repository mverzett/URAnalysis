#ifndef URGenericElectronsSelector_h
#define URGenericElectronsSelector_h



#include "URAnalysis/AnalysisFW/interface/URSelector.h"



template<typename Object, const std::vector< Object >& (URStreamer::*Collection)() >
class URGenericElectronsSelector: public URSelector
{
  public:
    URGenericElectronsSelector(const std::string name) : URSelector(name)
    {
      initialize();
    }

    virtual bool select(URStreamer& event)
    {
      int nElectrons = 0;
      selectedElectronCollection_.clear();
      for(auto electron = (event.*Collection)().begin(); electron != (event.*Collection)().end(); electron++)
      {
        if(select(*electron))
        {
          selectedElectronCollection_.push_back(&(*electron));
          nElectrons++;
        }
      }
      if(nElectrons >= minNElectrons_)
        return true;
      return false;
    }
    
    bool select(const Object& electron)
    {
      if(electron.Pt() > electronPtMin_ &&
        fabs(electron.Eta()) < electronEtaMax_)
      {
        return (this->*electronSelection_)(electron);
      }
      return false;
    }
    
    std::vector< const Object* > getSelectedElectrons()
    {
      return selectedElectronCollection_;
    }
      
    void configure() override
    {
      URSelector::configure();
      if(!isConfigured_)
      {    
        addCfgParameter<double>("electronPtMin", "Minimum pt threshold of electron selection.");
        addCfgParameter<double>("electronEtaMax", "Maximum eta threshold of electron selection.");
        addCfgParameter<int>("minNElectrons", "Minimum number of good electrons required per event.");
        addCfgParameter<std::string>("electronSelectionName", "Name of electron selection to apply.");
        
        registerConfiguration();
        
        electronPtMin_ = getCfgParameter<double>("electronPtMin");
        electronEtaMax_ = getCfgParameter<double>("electronEtaMax");
        minNElectrons_ = getCfgParameter<int>("minNElectrons");
        electronSelectionName_ = getCfgParameter<std::string>("electronSelectionName");
        
        setElectronSelection();
        
        isConfigured_ = true;
      }
    }
    
    typedef bool (URGenericElectronsSelector<Object, Collection>::*electronSelection)(const Object&); 
    
  private:
    void initialize()
    {
      isConfigured_ = false;
      electronPtMin_ = 0;
      electronEtaMax_ = 0;
      minNElectrons_ = 999;
      selectedElectronCollection_.clear();
      configure();
    }
    
    bool tightElectronSelection(const Object& electron)
    {
      // FIXME: It is a pass-through for the time being
      return true; 
    }
    
    bool passThroughElectronSelection(const Object& electron)
    {
      Logger::log().warning() << "W A R N I N G ! URGenericElectronsSelector: using pass-through muon selection! Please set correct selection type in cfg file!\n";
      return true;
    }
    
    void setElectronSelection()
    {
      if(!electronSelectionName_.compare("tight"))
        electronSelection_ = &URGenericElectronsSelector<Object, Collection>::tightElectronSelection;
      else
        electronSelection_ = &URGenericElectronsSelector<Object, Collection>::passThroughElectronSelection;
    }
    
    bool isConfigured_;
    double electronPtMin_;
    double electronEtaMax_;
    int minNElectrons_;
    std::string electronSelectionName_;
    electronSelection electronSelection_;
    std::vector< const Object* > selectedElectronCollection_;
};



#endif // URGenericElectronsSelector_h
