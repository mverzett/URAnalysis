#ifndef PDGID_h
#define PDGID_h

#include <unordered_map>
#include <string>

namespace ura{
  enum PDGID {
    d = 1,
    u = 2,
    s = 3,
    c = 4,
    b = 5,
    t = 6,

    dbar = -1,
    ubar = -2,
    sbar = -3,
    cbar = -4,
    bbar = -5,
    tbar = -6,
	
    e    	 = 11,
    nu_e 	 = 12,
    mu   	 = 13,
    nu_mu  = 14,
    tau    = 15,
    nu_tau = 16,

    ebar    	= -11,
    nubar_e 	= -12,
    mubar   	= -13,
    nubar_mu  = -14,
    nubar_tau = -16,
    taubar    = -15,

    gluon = 21,
    gamma = 22,
    Z = 23,
    Wplus = 24,
    Wminus = -24,
    H = 25
  };

  const std::unordered_map<int, std::string> pdg_names = {
    {1, "d"},
    {2, "u"},
    {3, "s"},
    {4, "c"},
    {5, "b"},
    {6, "t"},
    {-1, "dbar"},
    {-2, "ubar"},
    {-3, "sbar"},
    {-4, "cbar"},
    {-5, "bbar"},
    {-6, "tbar"},	
    {11, "e    	"},
    {12, "nu_e 	"},
    {13, "mu   	"},
    {14, "nu_mu "},
    {15, "tau   "},
    {16, "nu_tau"},
    {-11, "ebar     "},
    {-12, "nubar_e  "},
    {-13, "mubar    "},
    {-14, "nubar_mu "},
    {-16, "nubar_tau"},
    {-15, "taubar   "},
    { 21, "gluon"},
    { 22, "gamma"},
    { 23, "Z"},
    { 24, "Wplus"},
    {-24, "Wminus"},
    { 25, "H"},
  };
}

#endif
