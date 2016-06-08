#ifndef HWARDS
#define HWARDS

#include "TDirectory.h"
#include "TH1.h"

class HistoOwnershipWard {
public:
	//simple class that ensures you turn off TH1::AddDirectory(false) once you don't need it
	HistoOwnershipWard() {
		TH1::AddDirectory(false);
	}
	~HistoOwnershipWard() {
		TH1::AddDirectory(true);
	}
};

class DirectoryWard {
	//simple class that ensures you go back to the same context (gDirectory) as when you created it
private:
	TDirectory *context_;
public:
	DirectoryWard():
		context_(gDirectory) {}
	~DirectoryWard() {
		context_->cd();
	}
};
#endif
