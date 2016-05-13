#ifndef URSelector_h
#define URSelector_h

#include <string>
#include <iostream>

#include "URAnalysis/AnalysisFW/interface/URParser.h"
#include "URAnalysis/AnalysisFW/interface/Logger.h"



class URStreamer;
class Muon;
class Electron;
class Jet;
class MET;

class URSelector
{
  public:
//     URSelector(){text_=""; baseIsConfigured = false;};
    URSelector(const std::string name) : name_(name) {baseIsConfigured_ = false;};
    URSelector& operator||(URSelector& other);
    URSelector& operator&&(URSelector& other);
    virtual bool select(URStreamer& event);
    virtual bool select(const Muon& muon);
    virtual bool select(const Electron& electron);
    virtual bool select(const Jet& jet);
    virtual bool select(const MET& met);
    virtual URSelector* first();
    virtual URSelector* second();
    
    void registerConfiguration(); 

    template<typename T>
    void addCfgParameter(const std::string parameterName, const std::string description)
    {
      URParser& parser = URParser::instance();
      opts::options_description& options = parser.optionGroup(getName().c_str(), getName() + " options.\n", URParser::CFG);
      options.add_options() 
        ((getName()+"."+parameterName).c_str(), opts::value< T >(), description.c_str());
    }

    template<typename T>
    void addCfgParameter(const std::string parameterName, const std::string description, T def_value)
    {
      URParser& parser = URParser::instance();
      opts::options_description& options = parser.optionGroup(getName().c_str(), getName() + " options.\n", URParser::CFG);
      options.add_options() 
        ((getName()+"."+parameterName).c_str(), opts::value< T >()->default_value(def_value), description.c_str());
    }

    template<typename T>
    T getCfgParameter(const std::string parameterName)
    {
      URParser& parser = URParser::instance();
      std::string optionName = getName()+"."+parameterName;

      try {
        const T result = (parser.values())[optionName].as<T>();
        return result;
      }
      catch (std::exception& e) {
        std::cerr << "Got " << e.what() << 
          " trying to retrieve cfg parameter named: " << optionName << std::endl;
        throw 42;
      }
    }

    virtual void configure();
    
    std::string getName() {return name_;}
    
//     struct CfgParameter
//     {
//       char* parameterName;
//       opts::value_semantic valueType;
//       char* description;
//     };
    
//     typedef bool (URSelector::*muonSelection)(const Muon&);
//     typedef bool (URSelector::*electronSelection)(const Electron&);
//     typedef bool (URSelector::*jetSelection)(const Jet&);
//     typedef bool (URSelector::*metSelection)(const MET&);
    
  private:
    const std::string name_;
    bool baseIsConfigured_;
    opts::options_description cfgParameters_;
};



class URSelectorOR: public URSelector
{
  public:
    URSelectorOR(URSelector& first, URSelector& second): URSelector(first.getName()+"OR"+second.getName()), first_(&first), second_(&second) {};
    virtual bool select(URStreamer& event){return (first_->select(event))||(second_->select(event));};
    URSelector* first()
    {
      return first_;
    }
    URSelector* second()
    {
      return second_;
    }
    

  private:
    URSelector* first_;
    URSelector* second_;
};
 


class URSelectorAND: public URSelector
{
  public:
    URSelectorAND(URSelector& first, URSelector& second): URSelector(first.getName()+"AND"+second.getName()), first_(&first), second_(&second) {};
    virtual bool select(URStreamer& event){return (first_->select(event))&&(second_->select(event));};
    URSelector* first()
    {
      return first_;
    }
    URSelector* second()
    {
      return second_;
    }

  private:
    URSelector* first_;
    URSelector* second_;
};



#endif // URSelector_h

