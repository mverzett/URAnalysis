#ifndef URGenericMuonsAndJetsSelector_h
#define URGenericMuonsAndJetsSelector_h



#include "URAnalysis/AnalysisFW/interface/URGenericMuonsSelector.h"
#include "URAnalysis/AnalysisFW/interface/URGenericJetsSelector.h"



template<typename Muon, const std::vector< Muon >& (URStreamer::*MuonCollection)(), typename Jet, const std::vector< Jet >& (URStreamer::*JetCollection)() >
class URGenericMuonsAndJetsSelector : public URGenericMuonsSelector<Muon, MuonCollection>, public URGenericJetsSelector<Jet, JetCollection>
{
public:
  URGenericMuonsAndJetsSelector(const std::string name): URGenericMuonsSelector<Muon, MuonCollection>(name), URGenericJetsSelector<Jet, JetCollection>(name) {};
  virtual bool select(URStreamer& event)
  {
    if(!URGenericMuonsSelector<Muon, MuonCollection>::select(event))
    {
      return false;
    }
    if(!URGenericJetsSelector<Jet, JetCollection>::select(event))
    {
      return false;
    }
    return true;
  }
private:
  
};



#endif // URGenericMuonsAndJetsSelector_h
