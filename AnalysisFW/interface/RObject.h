#ifndef RObject_h
#define RObject_h

#include "TObject.h"
#include "TH1F.h"
#include "TH1D.h"
#include "TH2F.h"
#include "TH2D.h"

#include <memory>
#include "URAnalysis/AnalysisFW/interface/Logger.h"

#include <tuple>

class RObject {
public:
  enum Type {T_UNKNOWN, T_TH1F, T_TH1D, T_TH2F, T_TH2D};

	template <class T, typename ... Args>
	static RObject book(Args ... args)
	{
		T* obj = new T(args ...);
		preprocess(obj);
		return RObject(
			obj,
			getType<T>()
			);
	}
	RObject(RObject const& other)
	{
		*this = other;
	}
	RObject():
		robj_(NULL),
    type_(T_UNKNOWN){}

  // void operator=(RObject const& other)
	// {
	// 	robj_ = other.robj_;
	// 	type_ = other.type();
	// }

	//Type getters
	template <class T>
	static Type getType() {return Type::T_UNKNOWN;}

	~RObject(){};

	void fill() {} //No need for now
	void fill(float x) {
		switch(type_){
		case Type::T_TH1F: tfill<TH1F>(x); break;
		case Type::T_TH1D: tfill<TH1D>(x); break;
		case Type::T_TH2F: break;
		case Type::T_TH2D: break;
    case Type::T_UNKNOWN: robj_.get()->GetName(); //this will crash!
		}
	}

	void fill(float x, float y) {
		switch(type_){
		case Type::T_TH1F: tfill<TH1F>(x, y); break;
		case Type::T_TH1D: tfill<TH1D>(x, y); break;
		case Type::T_TH2F: break;
		case Type::T_TH2D: break;
    case Type::T_UNKNOWN: robj_.get()->GetName(); //this will crash!
		}
	}

	void fill(float x, float y, float z) {
		switch(type_){
    case Type::T_TH1F: break;
    case Type::T_TH1D: break;
		case Type::T_TH2F: tfill<TH2F>(x, y); break;
		case Type::T_TH2D: tfill<TH2D>(x, y); break;
    case Type::T_UNKNOWN: robj_.get()->GetName(); //this will crash!
		}
	}

	/*/helper struct for partial template specialization
	template<Type T, class ... Args>
	struct Filler {
		static void fill(RObject &obj, Args ... args){
			Logger::log().error() << "Wrong template specialization!" << endl;
		}
		};*/

	template<class T, class ... Args> 
	void tfill(Args ... args)
	{
		getAs<T>()->Fill(args ...); 
	}

	TObject *get() const {return robj_.get();}  
	template<class T>
	T* getAs() const {return dynamic_cast<T*>(get());}
	Type     type() const {return type_;} 

private:
  RObject(TObject *obj, Type type):
		robj_(obj),
		type_(type){}
		
	template<class T>
	static void preprocess(T* obj) {obj->Sumw2();}
	
	std::shared_ptr<TObject> robj_;
  Type type_;
};

//template specialization
template <> RObject::Type RObject::getType<TH1F>() {return RObject::Type::T_TH1F;}
template <> RObject::Type RObject::getType<TH1D>() {return RObject::Type::T_TH1D;}
template <> RObject::Type RObject::getType<TH2F>() {return RObject::Type::T_TH2F;}
template <> RObject::Type RObject::getType<TH2D>() {return RObject::Type::T_TH2D;}

#endif
