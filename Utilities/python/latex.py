from math import log10, floor
from pdb import set_trace
ends_ = set([' ', '}'])
starts_ = set(['#', '_', '^'])

def pippo():
	pass

def tokenize(string):
	tokens = []
	token = []
	for c in string:
		if c in ends_:
			token.append(c)
			tokens.append(''.join(token))
			token = []
		elif c in starts_:
			tokens.append(''.join(token))
			token = [c]
		else:
			token.append(c)
	tokens.append(''.join(token))
	return tokens

def tlatex_convert(tokens):
	ret = []
	for tok in tokens:
		if not tok: continue
		elif tok[0] == '#':
			ret.append('$\%s$'% tok[1:])
		elif tok[0] in starts_:
			ret.append('$\%s$'% tok)
		else:
			ret.append(tok)
	return ''.join(ret)

def t2latex(string):
	'''converts TLatex into valid latex'''
	return tlatex_convert(tokenize(string))

def format_with_error(val, err, valonly=False, erronly=False):
	err_mag = int(floor(log10(err))) -1
	if err_mag >= 0:
		vv = round(val, -1*err_mag)
		ee = round(err, -1*err_mag)
		if valonly:
			return '$%d$' % (vv)
		elif erronly:
			return '$\pm %d$' % (ee)
		else:
			return '$%d \pm %d$' % (vv, ee)
	else:
		err_mag = abs(err_mag)
		format = '%.'+str(err_mag)+'f'
		if valonly:
			return '$%s$' % (format % val)
		elif erronly:
			return '$\pm %s$' % (format % err)
		else:
			return '$ %s $' % (' \pm '.join([format % val, format % err]))

def format_with_asym_error(val, errup, errdw, valonly=False, erronly=False):
	minerr = min(errup, -1*errdw)
	err_mag = int(floor(log10(minerr))) -1
	if err_mag >= 0:
		vv = round(val, -1*err_mag)
		eu = round(errup, -1*err_mag)
		ed = round(errdw, -1*err_mag)
		if valonly:
			return '$%d$' % vv
		elif erronly:
			return '$^{+%d}_{%d}$' % (eu, ed)
		else:
			return '$%d^{+%d}_{%d}$' % (vv, eu, ed)
	else:
		err_mag = abs(err_mag)
		format = '%.'+str(err_mag)+'f'
		if valonly:
			return '$%s$' % (format % val)
		elif erronly:
			return '$^{+%s}_{%s}$' % (format % errup, format % errdw)
		else:
			return '$%s^{+%s}_{%s}$' % (format % val, format % errup, format % errdw)
		
def format_roovar(rvar, asymm_err=False, valonly=False, erronly=False):
	value = rvar.value
	if asymm_err:
		eu, ed = rvar.error if hasattr(rvar.error, '__len__') else (rvar.error, -1*rvar.error)
		return format_with_asym_error(value, eu, ed, valonly=valonly, erronly=erronly) 
	else:
		error = rvar.error if not hasattr(rvar.error, '__len__') else max(abs(i) for i in rvar.error)
		return format_with_error(value, error)

def tabline(elems, convert=True):
	els = [t2latex(i) if convert else i for i in elems]
	return '%s \\\\ \n' % (' & '.join(els))
