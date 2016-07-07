from rootpy.plotting import views

class NormalizedView(views._FolderView):
	'returns a normalized version of the plot'
	def __init__(self, directory):
		super(NormalizedView, self).__init__(directory)
		
	def apply_view(self, thingy):
		# Set in base class
		clone = thingy.Clone()
		clone.Scale(1./clone.Integral())
		return clone
