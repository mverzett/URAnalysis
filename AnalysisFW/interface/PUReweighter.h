#ifndef PUReweighter_h
#define PUReweighter_h

#include <vector>
#include <string>

class PUReweighter{
public:
	
  PUReweighter():
    weights_(),
    wsize_() {}
    void init(std::string sample_fname, std::string data_fname="data.meta.pu.root", std::string hdata="pileup", std::string hmc="pu_distribution");

	float weight(size_t nvtx){
		return (nvtx < wsize_) ? weights_[nvtx] : weights_[wsize_-1];
	}

private:
	std::vector<float> weights_;
	size_t wsize_; //store to avoid computing every time
};

#endif
