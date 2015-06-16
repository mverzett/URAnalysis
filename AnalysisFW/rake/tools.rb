
#Set of tools to be used in a rakefile

# Cool debug patch from 
# http://martinfowler.com/articles/rake.html
class Task 
  def investigation
    result = "------------------------------\n"
    result << "Investigating #{name}\n" 
    result << "class: #{self.class}\n"
    result <<  "task needed: #{needed?}\n"
    result <<  "timestamp: #{timestamp}\n"
    result << "pre-requisites: \n"
    prereqs = @prerequisites.collect {|name| Task[name]}
    prereqs.sort! {|a,b| a.timestamp <=> b.timestamp}
    prereqs.each do |p|
      result << "--#{p.name} (#{p.timestamp})\n"
    end
    latest_prereq = @prerequisites.collect{|n| Task[n].timestamp}.max
    result <<  "latest-prerequisite time: #{latest_prereq}\n"
    result << "................................\n\n"
    return result
  end
end

def compile_string(includes, libs, src, trgt)
  #FNAL LPC patch for boost
  fnal_include = ''
  fnal_libs = ''
  if ENV['HOSTNAME'].include? "fnal.gov"
    #assume we are using CMSSW
    fnal_include="-I/cvmfs/cms.cern.ch/#{ENV['SCRAM_ARCH']}/external/boost/1.57.0/include/ -I/cvmfs/cms.cern.ch/#{ENV['SCRAM_ARCH']}/external/lhapdf6/6.1.5/include"
    fnal_libs="-L/cvmfs/cms.cern.ch/#{ENV['SCRAM_ARCH']}/external/boost/1.57.0/lib/ -L/cvmfs/cms.cern.ch/#{ENV['SCRAM_ARCH']}/external/lhapdf6/6.1.5/lib"
  end
  return "g++ -g -std=c++11 -Wl,--no-as-needed #{fnal_include} #{includes.map{|x| '-I'+x}.join(' ')} `root-config --cflags` `root-config --libs` -lMinuit #{fnal_libs} -lLHAPDF -lboost_program_options #{libs.join(' ')} #{src} -o #{trgt}"
end
     

def make_obj_task(source, dependencies, *include_dirs)
  target = source.sub(%r{(.*)/src/([^/.]*).(cc|C|cxx)},"\\1/lib/\\2.o")
  file target => dependencies+[source] do |t|
    #puts target
    #FNAL LPC patch for boost
    fnal_include = ''
    if ENV['HOSTNAME'].include? "fnal.gov"
      #assume we are using CMSSW
      fnal_include="-I/cvmfs/cms.cern.ch/#{ENV['SCRAM_ARCH']}/external/boost/1.57.0/include/ -I/cvmfs/cms.cern.ch/#{ENV['SCRAM_ARCH']}/external/lhapdf6/6.1.5/include"
    end
    sh "g++ #{include_dirs.map{|x| "-I#{x}"}.join(' ')} #{fnal_include} `root-config --cflags` -Wall -c #{source} -o #{target}"
  end
  return target
end

def make_libs(project_dir, deps='')
  #list all the .cc .C and .cxx files to be compiled  
  to_be_compiled = Dir.glob("#{project_dir}/src/*").select{|x| %r{#{project_dir}/src/(.*).(cc|C|cxx)$}.match(x)}
  #list all the headers
  headers = Dir.glob("#{project_dir}/interface/*.h")
  #for each file make a .o file task
  if deps == ''
    targets = to_be_compiled.map{|x| make_obj_task(x, headers, "#{project_dir}/interface/")}
  else
    targets = to_be_compiled.map{|x| make_obj_task(x, headers, "#{project_dir}/interface/", "#{deps}/interface/")}
  end
  #and put it in the timestamp task
  lib_timestamp = "#{project_dir}/lib/.lib_timestamp"
  file lib_timestamp => targets do |t|
    puts t.investigation
    sh "touch #{t.name}"
  end
  return lib_timestamp
end

def compile_analyzer(source, libs='', *deps)
  target = "bin/#{source.split('.')[0]}.exe"
  file target => [source, *deps] do |t|
    project_dir = ENV['URA_PROJECT']
    fwk_dir = ENV['URA']+'/AnalysisFW'
    local_libs = Dir.glob("#{project_dir}/lib/*.*o").join(" ")
    fwk_libs = Dir.glob("#{fwk_dir}/lib/*.*o").join(" ")
    libs += "#{local_libs} #{fwk_libs}"

    local_includes = "#{project_dir}/interface/"
    fwk_includes = "#{fwk_dir}/interface/"

    sh compile_string([local_includes, fwk_includes],local_libs+fwk_libs, source, t.name)
    puts t.investigation
  end 
end

def new_trial(res_dir, plot_dir, label='')
  timestamp = Time.now.strftime("%Y%b%d")
  if not res_dir.empty?
    full_res  = "results/#{$jobid}/#{res_dir}"
    if File.exist? full_res
      if not File.symlink? full_res
        throw "#{full_res} MUST be a symlink in the first place to work!"
      end
      sh "rm -f #{full_res}"
    end
    
    #add new dir and new link
    chdir("results/#{$jobid}") do
      new_res = "#{res_dir}_#{timestamp}_#{label}"
      sh "mkdir -p #{new_res}" 
      sh "ln -s #{new_res} #{res_dir}"
    end
  end

  if not plot_dir.empty?
    full_plot = "plots/#{$jobid}/#{plot_dir}"
    if File.exist? full_plot 
      if not File.symlink? full_plot
        throw "#{full_plot} MUST be a symlink in the first place to work!"
      end
      sh "rm -f #{full_plot}"    
    end
    
    chdir("plots/#{$jobid}") do
      new_plot = "#{plot_dir}_#{timestamp}_#{label}"
      sh "mkdir -p #{new_plot}" 
      sh "ln -s #{new_plot} #{plot_dir}"
    end
  end
end

def publish_pics(input_name, output_name)
  puts input_name, output_name
  puts File.directory? output_name
  if not (File.directory? output_name)
    sh "mkdir #{output_name}"
  end
  Dir["#{input_name}/*"].each do |path|
    if File.directory? path
      bname = File.basename(path)
      newdir = "#{output_name}/#{bname}"
      publish_pics(path, newdir)
    elsif path.end_with? '.png'
      `cp #{path} #{output_name}/.`
    end
  end
end
