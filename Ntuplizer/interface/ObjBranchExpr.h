#ifndef ObjBranchExpr_H
#define ObjBranchExpr_H

#include "URAnalysis/Ntuplizer/interface/ObjExpression.h"
#include "URAnalysis/Utilities/interface/typeConversion.h"
#include "URAnalysis/Ntuplizer/interface/EventTree.h"
#include "TTree.h"
#include <vector>
#include <iostream>
#include <memory>

/*
class: ObjBranchExpr<EDObject, VType>

This class provides the implementation of a single element TTree branch filled 
with a StringObjectFunction. 
The first template argument defines the EDObject on which the functor operates,
while the second template provides the output collection type.

WARNING: As every return value computed by StringObjectFunction () operator is
by default a double, rounding errors for big numbers WILL happen. This makes
this option not suitable for long ints and similar where every bit counts.
The final return value is just a type cast from double, in order to save space.

To evercome this effect the internal implementation of StringObjectFunction's
grammar should be changed, returning instead of the static_cast of the variable
the reinterpret_cast, but this gets beyond the scope of this framework and would 
break backward compatibility and the physical meaning of the number.

Author: Mauro Verzetti (UR)
 */

template <typename EDObject, typename Type>
class ObjBranchExpr: public ObjExpression<EDObject> {
public:
  ObjBranchExpr(BranchInfo &info, EventTree& tree, std::string &expr):
    ObjExpression<EDObject>(expr),
    branch_val_(),
    name_(info.name)
  {
    //std::cout<<name_ <<": set branch to vals addr: " << &branch_val_ << std::endl;
    //branch_ = tree.branch(info.name+info.str_type, &branch_val_);
    branch_ = tree.branch(info.name, &branch_val_, (info.name+info.str_type).c_str());
    //std::cout<<name_ <<": set branch to vals addr: " << &branch_val_ << std::endl;
  }

  ~ObjBranchExpr(){ /*delete branch_val_;*/ }
  virtual void fill(const EDObject &obj) {branch_val_ = ura::as<Type>(this->functor_(obj));}
  virtual void debug() {std::cout<<name_ <<" vals addr: "<< &branch_val_<< " branch addr: "<< (Type*) branch_->GetAddress() << std::endl;}

private:
  Type branch_val_;
  TBranch *branch_;
  std::string name_;
};

/*
function: ObjBranchExprFactory<EDObject>

This factory specializes the second template argument of ObjBranchExpr, 
providing the proper vector type according to the information encoded in
BranchInfo (defined in: URAnalysis/Ntuplizer/interface/ObjExpression.h).

Author: Mauro Verzetti (UR)
 */

template <typename EDObject>
ObjExpression<EDObject>* ObjBranchExprFactory(BranchInfo &info, EventTree& tree)
{
  switch(info.type){
  case BranchInfo::typeID::USHORT : return new ObjBranchExpr<EDObject, unsigned short>(info, tree, info.expr);
  case BranchInfo::typeID::DOUBLE : return new ObjBranchExpr<EDObject, double>(info, tree, info.expr);	       
  case BranchInfo::typeID::SHORT  : return new ObjBranchExpr<EDObject, short >(info, tree, info.expr);	       
  case BranchInfo::typeID::INT    : return new ObjBranchExpr<EDObject, int>(info, tree, info.expr);	       
  case BranchInfo::typeID::UINT   : return new ObjBranchExpr<EDObject, unsigned int>(info, tree, info.expr);  
  case BranchInfo::typeID::FLOAT  : return new ObjBranchExpr<EDObject, float>(info, tree, info.expr);	       
  case BranchInfo::typeID::LONG   : return new ObjBranchExpr<EDObject, long>(info, tree, info.expr);	       
  case BranchInfo::typeID::BOOL   : return new ObjBranchExpr<EDObject, bool>(info, tree, info.expr); 	       
  case BranchInfo::typeID::ULONG  : return new ObjBranchExpr<EDObject, unsigned long>(info, tree, info.expr); 
  default: return NULL;
  }
  //return ret;
}

#endif 
