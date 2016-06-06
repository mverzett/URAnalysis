#ifndef AnalyzerBase_cxx
#define AnalyzerBase_cxx

#include <typeinfo>

#include "URAnalysis/AnalysisFW/interface/AnalyzerBase.h"
#include "URAnalysis/AnalysisFW/interface/Logger.h"

AnalyzerBase::~AnalyzerBase()
{
  outFile_.Close();
	Logger::log().debug() << "AnalyzerBase: called dtor" << std::endl;
}

#endif // AnalyzerBase_cxx
