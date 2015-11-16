#ifndef URSelector_cc
#define URSelector_cc

#include "URSelector.h"



bool URSelector::select(URStreamer& event)
{
  Logger::log().warning() << "W A R N I N G ! URSelector::select(URStreamer&): Base class select method called!\n"; 
  return false;
}



bool URSelector::select(const Muon& muon)
{
  Logger::log().warning() << "W A R N I N G ! URSelector::select(const Muon&): Base class select method called!\n";
  return false;
}



bool URSelector::select(const Electron& electron)
{
  Logger::log().warning() << "W A R N I N G ! URSelector::select(const Electron&): Base class select method called!\n";
  return false;
}



bool URSelector::select(const Jet& jet)
{
  Logger::log().warning() << "W A R N I N G ! URSelector::select(const Jet&): Base class select method called!\n";
  return false;
}



bool URSelector::select(const MET& met)
{
  Logger::log().warning() << "W A R N I N G ! URSelector::select(const MET&): Base class select method called!\n";
  return false;
}



URSelector* URSelector::first()
{
  Logger::log().warning() << "W A R N I N G ! URSelector::first(): Base class select method called!\n";
  return this;
}



URSelector* URSelector::second()
{
  Logger::log().warning() << "W A R N I N G ! URSelector::second(): Base class select method called!\n";
  return this;
}



void URSelector::registerConfiguration()
{
  URParser& parser = URParser::instance();
  opts::options_description & options = parser.optionGroup(getName(), getName() + " options", URParser::CFG);

  for(auto it = cfgParameters_.options().begin(); it != cfgParameters_.options().end(); it++)
  {
    options.add(*it);
  }
  parser.parseArguments();
  parser.parseArguments();
}



void URSelector::configure()
{
  if(!baseIsConfigured_)
  {
    // here gets the getConfiguration
//     URParser& parser = URParser::instance();
    // Put any configuration parameters for the base class here
    
    baseIsConfigured_ = true;
  }
}



URSelector& URSelector::operator||(URSelector& other)
{
  URSelectorOR* result = new URSelectorOR(*this,other);
  return *result;
}



URSelector& URSelector::operator&&(URSelector& other)
{
  URSelectorAND* result = new URSelectorAND(*this,other);
  return *result;
}



#endif // URSelector_cc
