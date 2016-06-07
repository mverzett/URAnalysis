import FWCore.ParameterSet.Config as cms

def diff(one, two):
	one_lines = one.__repr__().split('\n')
	two_lines = two.__repr__().split('\n')
	max_len = max(len(i) for i in one_lines)
	format = '%-'+str(max_len)+'s'
	for i, j in zip(one_lines, two_lines):
		sep = ' ' if i == j else '|'
		print format % i, sep, j

def rec_diff(one, two):
	'recursive checks for the same parameters'
	if not isinstance(one, type(two)):
		return [('', '%s' % type(one), '%s' % type(two))]
	elif isinstance(one, (cms.PSet, cms.EDProducer, cms.EDAnalyzer, cms.EDFilter)):
		two_pars = set(two.parameterNames_())
		one_pars = set(one.parameterNames_())
		diffs = []
		for pname in one_pars:
			if pname in two_pars:
				deeper = rec_diff(getattr(one, pname), getattr(two, pname))
				diffs.extend([
						('%s.%s' % (pname, i), j, k) for i,j,k in deeper if i is not None
						])
			else:
				diffs.append((
						pname, '%s' % getattr(one, pname), '--'))
		missing = two_pars - one_pars
		for pname in missing:
			diffs.append((mis, '--', '%s' % getattr(two, pname)))
		return diffs
	elif isinstance(one, cms.VPSet):
		raise RuntimeError('still to implement on VPSet!')
	else:
		if one == two:
			return [(None, None, None)]
		else:
			return [('',  '%s' % one, '%s' % two)]
	pass

def better_diff(one, two):
	diffs = rec_diff(one, two)
	for i,j,k in diffs:
		print i, ":  ", j, '-->', k

