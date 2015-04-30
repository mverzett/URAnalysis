if which ruby >/dev/null && which gem >/dev/null; then
    if which rake >/dev/null; then
	echo "rake already set up, nothing to do here!"
    else
	gemspath=`ruby -rubygems -e 'puts Gem.user_dir'`
	if [ -e $gemspath/bin/rake ]; then
	    echo "rake already installed"
	    echo "source environment.sh to activate it"
	    echo "or automatically set it up in .bash_profile"
	else
	    echo "installing rake..."
	    gem install --user-install rake
	    echo "..done, source environment to let it take effect"
	fi
    fi
else
    echo "ruby not present! You have to install it locally with RVM"
    echo "(not automatically supported yet)"
    exit 1
fi