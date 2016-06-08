#ifndef AnalyzerBase_h
#define AnalyzerBase_h

//#include "AnalyzerBase.C"
//FIXME: this should NOT be here
//#include "../../AnalysisTools/scripts/URStreamer.h"
// #include "../../AnalysisTools/scripts/Dict.cxx"
//#include "HistoPlotter.C"

//class URSelector;

#include <string>
#include "TFile.h"
#include "TTree.h"
#include "URAnalysis/AnalysisFW/interface/Logger.h"

class AnalyzerBase
{
public:
  AnalyzerBase(const std::string myName, const std::string output_name):
    myName_(myName),
    outFile_(output_name.c_str(), "recreate"),
    tree_(0)
  {
};
  ~AnalyzerBase();
     
  // To be run inside the thread
  virtual void analyze() = 0; 
  virtual void begin() = 0;
  virtual void end() {
		outFile_.Write();
		Logger::log().debug() << "AnalyzerBase::end" << std::endl;
	}
    
  // To be run at the end
  virtual void postProcess() {}

  //must implement also this
  //static void setOptions()

  void setTree(TTree* tree){tree_=tree;}
    
private:
  std::string myName_;
    
protected:
  //URStreamer* event;
//     URSelector* s;
  TFile outFile_;
  TTree* tree_;
};

#endif // AnalyzerBase_h
