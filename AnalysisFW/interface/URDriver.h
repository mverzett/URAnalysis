#ifndef URDriver_h
#define URDriver_h

/*
class URDriver<T> T = Analyzer

Class to handle the analysis of Ntuples in a threaded way
 */

#include "URParser.h"
#include "PathReader.h"
#include "SafeQueue.h"
#include <vector>
#include "Worker.h"
#include <stdio.h>
#include "TFileMerger.h"
#include <iostream>
#include <stdio.h>
#include "TFile.h"
#include "TTree.h"
#include "Logger.h"
#include <sstream>
#include "TThread.h"
#include "TROOT.h"
#include "ProgressBar.h"
#include "TTreeCache.h"

// Necessary to take a shell variable as cpp macro and transform it into a string
#define TOSTRING(s) STRINGIFY(s)
#define STRINGIFY(s) #s

template<typename T>
class AnalysisWorker: public Worker{
public:
  AnalysisWorker(std::string id, std::string outname):
    Worker(id),
    analyzer_(outname)
  {    
		Logger::log().debug() << id_ << ": Initializing analyzer" << std::endl;
    analyzer_.begin();
  }

	void setTree(TTree* tree) {analyzer_.setTree(tree);}
	void end() {analyzer_.end();}

	void start_nothread(SafeQueue<std::string>& inputs_, ProgressBar &bar_) 
	{
    while(!inputs_.empty())
    {
      //get input file name from the queue
      std::string input_file = inputs_.pop();
      Logger::log().debug() << id_ << ": got input file: " <<
				input_file << std::endl;

      //open and read it
      TFile *file = TFile::Open(input_file.c_str());
			if(file){
				TTree *tree = (TTree*) file->Get("Events");
				
				if(tree){
					//assign to analyzer
					TTreeCache::SetLearnEntries(200);
					tree->SetCacheSize(10000000);
					setTree(tree);
					work();
				} else {
					Logger::log().error() << id_ << ": could not read the tree in " <<
						input_file << " properly" << std::endl;
          throw 42;
				}
			} else {
				Logger::log().error() << id_ << ": could not open file" <<
					input_file << " properly" << std::endl;
        throw 42;
			}
      file->Close();
      bar_.update();
    }
    Logger::log().debug() << id_ <<
      "No more files to analyze, exiting" << std::endl;		
		end();
	}

private:
  virtual void work(){ analyzer_.analyze(); }
  T analyzer_;
};

template<typename T>
class URDriver{
public:
  URDriver():
    reader_()
  {
    //define CLI and CFG options
    URParser &parser = URParser::instance();
    opts::options_description &opts = parser.optionGroup("processing", "CLI and CFG options on how to run the analyzer");
    opts::positional_options_description &args = parser.args();

    opts.add_options()
      ("input", opts::value<std::string>(), "path of the file containing the list of root files to be processed")
      ("output", opts::value<std::string>(), "path of the root file to be produced")
      ("threads", opts::value<int>()->default_value(2), "number of threads to be used for processing")
      ("J", opts::value<int>()->default_value(1), "total number of jobs")
      ("j", opts::value<int>()->default_value(0), "jobnumber");
	  ("noprog", "do not show progress bar");
    //make input and output positional (even though are still valid in CLI)
    args.add("input", 1);
    args.add("output", 1);

    opts::options_description &generic = parser.optionGroup("generic");
    generic.add_options()
      ("verbose,v", "prints debugging output")
      ("quiet,q", "less printout");

    //set logger level
    Logger::log().setLevel(Logger::Level::WARNING);
  }


  //this does mostly what a main would do, saving you to write it again every new analyzer
  int run()
  {
    T::setOptions();
    URParser &parser = URParser::instance();
    parser.parseArguments();
    opts::variables_map &values = parser.values();

    if(values.count("verbose"))
    {
      Logger::log().warning() << "Setting the log level to DEBUG. " <<
				"Brace yourselves, printout madness is coming!" << std::endl;
      Logger::log().setLevel(Logger::Level::DEBUG);
    }
    if(values.count("quiet"))
    {
      Logger::log().warning() << "Setting the log level to FATAL. " <<
				"To be as quiet as possible!" << std::endl;
      Logger::log().setLevel(Logger::Level::FATAL);
    }

    //FIXME: should test that lack of input raises error
    //Get options and fill input file queue
    SafeQueue<std::string> input_files;
    std::string file_list = values["input"].as<std::string>();
    std::string output_file = values["output"].as<std::string>();
    Logger::log().debug() << "Input file is: " << file_list << 
      std::endl << "Output file is: " << output_file << std::endl;
    const int njobs = values["J"].as<int>();
    const int njob = values["j"].as<int>();

    long int nfiles = reader_.fill(input_files, file_list, njob, njobs);
    //create brogress bar, update it every 5 files, to be faster
    ProgressBar progbar(nfiles, 1, !values.count("noprog")); 

    const int n_threads = values["threads"].as<int>();
    Logger::log().debug() << "Running with " << n_threads << " threads"<< std::endl;

    //create (but do NOT use) a TThread, to trigger the spotless and 
    //clean ROOT implementation to consider thread safety a priority
    //and protect the global variables (!)
    TThread dummy;

    //create threads with unique names
    AnalysisWorker<T> *workers[n_threads];
	std::vector<std::string> outputs;
	//workers.reserve(n_threads);
	for(int i=0; i<n_threads; i++)
	{
		std::string outname(output_file);
		if(n_threads != 1)
		{
			outname = std::tmpnam(NULL);
			outname += ".root";
			Logger::log().debug() << "Output file of thread " << i <<
				"will be: " << outname << std::endl;
		}

		std::ostringstream id;
		id << "AnalysisWorker_" << i;
		workers[i] = new AnalysisWorker<T>(id.str(), outname);
		outputs.push_back(outname);
	}

    //run threads, wait for them to finish and free memory
		if(n_threads > 1){
			/* Poor man's version of threading, imposed 
				 by ROOT standards to open TFiles sequentially
				 For the original (and better) version look
				 into waitForROOT6 branch!

				 - Loop over all the input files
				   - open one for every thread (if available) 
					   and set the tree to the analyzer
					 - Run the threads in parallel
				 - At file termination call end 
			*/
			while(!input_files.empty())
			{
				TFile *files[n_threads];// = {};
				int counter = 0;
				while(counter < n_threads && !input_files.empty())
				{
					//get input file name from the queue
					std::string input_file = input_files.pop();
					Logger::log().debug() << ": got input file: " <<
						input_file << std::endl;

					//open and read it
					TFile *file = TFile::Open(input_file.c_str());
					Logger::log().debug() << "Input file is open? " << 
						file->IsOpen() << endl;
					if(file)
					{
						files[counter] = file;
						TTree *tree = (TTree*) file->Get("Events");
						if(tree)
						{
							TTreeCache::SetLearnEntries(200);
							tree->SetCacheSize(10000000);
							//assign to analyzer
							workers[counter]->setTree(tree);
							counter++;
						} 
						else 
						{
							Logger::log().error() << ": could not read the tree in " <<
								input_file << " properly" << std::endl;
							file->Close();
              throw 42;
						}
					} 
					else 
					{
						Logger::log().error() << ": could not open file" <<
							input_file << " properly" << std::endl;
            throw 42;
					}
				}//while(counter < n_threads && !input_files.empty())
						
				Logger::log().debug() << "Starting " << counter << " threads" << std::endl;
				for(int i=0; i<counter; i++) workers[i]->start();
			
				for(int i=0; i<counter; i++) 
				{
					Logger::log().debug() << "Waiting for thread "<< i <<" to finish..." << std::endl;
					workers[i]->join();
					Logger::log().debug() << "Thread "<< i <<" done!" << std::endl;
					progbar.update();
				}
				for(int i=0; i<counter; i++) files[i]->Close();
			}//while(!input_files.empty())
			Logger::log().debug() << "No more files to analyze, exiting" << std::endl;
			for(int i=0; i<n_threads; i++) workers[i]->end();
		} //if(n_threads > 1)
		else 
		{
			Logger::log().debug() << "Starting without threads!" << std::endl;
			workers[0]->start_nothread(input_files, progbar);
		}
		for(int i=0; i<n_threads; i++) delete workers[i];
    
    //merge the files
		if(n_threads!=1)
		{
			Logger::log().debug() << "Merging output files..." << std::endl;
			TFileMerger merger;
			merger.OutputFile(output_file.c_str());
			for(auto& file : outputs) merger.AddFile(file.c_str(), false); //why false? no clue, copied from old fwk
			bool isMerged = merger.Merge();

			if(!isMerged)
			{
				Logger::log().fatal() <<"Error in merging thread outputs!" << std::endl;
				throw 42;
			}
		}
    
    // for(auto& file : outputs) 
    // {
    //   if(!remove(file.c_str()))
    //   {
    // 	Logger::log().fatal() <<"Error removing file: " << file << std::endl;
    // 	throw 42;
    //   }
    // }
    return 0;
  }
private:
  PathReader reader_;
};

#endif
