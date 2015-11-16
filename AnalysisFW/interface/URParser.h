#ifndef URParser_h
#define URParser_h

#include <boost/program_options.hpp>
#include <map>
#include <string>
#include <exception>
#include <iostream>
#include "Logger.h"
namespace opts = boost::program_options;

/*
  Class: URParser
  Singleton wrapper around boost/program_options library, which does most of the job
*/

class URParser
{
public:
  //option visibility (everywhere, command line only, cfg only)
  enum Visibility {ALL, CLI, CFG};

  void parseArguments();
  //void parseCfg()
  opts::options_description & optionGroup(std::string groupName, std::string desc="", Visibility vis=ALL);
  opts::positional_options_description & args(){return args_;}
  opts::variables_map & values() {return vmap_;}
  opts::basic_parsed_options<char> cfg_options() {return cfg_options_;};

  void setArgs(int argc, char** argv){argc_=argc; argv_=const_cast<char**>(argv);}

  template<typename T>
  void addCfgParameter(const std::string group, const std::string parameterName, const std::string description) {
    URParser& parser = URParser::instance();
    opts::options_description& options = parser.optionGroup(group.c_str(), group + " options.\n", Visibility::CFG);
    options.add_options() 
      ((group+"."+parameterName).c_str(), opts::value< T >(), description.c_str());
  }
  
  template<typename T>
  void addCfgParameter(const std::string group, const std::string parameterName, const std::string description, T def_value) {
    URParser& parser = URParser::instance();
    opts::options_description& options = parser.optionGroup(group.c_str(), group + " options.\n", Visibility::CFG);
    options.add_options() 
      ((group+"."+parameterName).c_str(), opts::value< T >()->default_value(def_value), description.c_str());
  }

	template<typename T>
	T getCfgPar(std::string name) {
		//makes better exception handling
		try {
			return vmap_[name].as<T>();
		}
		catch (std::exception& e) {
			std::cerr << "Got " << e.what() << 
				" trying to retrieve cfg parameter named: " << name << std::endl;
			throw 42;
		}
	}

	template<typename T>
	T getCfgPar(std::string group, std::string name) { return getCfgPar<T>(group+"."+name);}

  // This must be a singleton
  static URParser& instance() {
    static URParser val;
    return val; 
  }
  static URParser& instance(int argc, char** argv) {
    URParser &val = URParser::instance();
    val.setArgs(argc, argv);
    return val;
  }

private:
  URParser():
    opts_(),
    args_(),
    cfg_options_(0),
    argc_(0),
    argv_(0)
  {
    opts::options_description &generic = optionGroup("generic", "general-purpose command-line-only options", CLI);
    generic.add_options()
      ("help,h", "produce help message")
      ("config,c", opts::value<std::string>(),"name of a file of a configuration.");
  }

  void help();

  struct OptionGroup{
    OptionGroup(std::string &groupName, std::string desc, Visibility vis):
      help(desc),
      value(groupName),
      visibility(vis)
    {}
    std::string help;
    opts::options_description value;
    Visibility visibility;
  };

  //No need to implement those
  URParser(URParser const&);
  void operator=(URParser const&);

  //non-positional options (grouped)
  std::map<std::string, OptionGroup> opts_;
    
  //positional args
  opts::positional_options_description args_; 
  
  opts::variables_map vmap_;
  opts::basic_parsed_options<char> cfg_options_;

  int argc_;
  char** argv_;
};

#endif
