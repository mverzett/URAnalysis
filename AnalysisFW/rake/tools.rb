
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

def scram_build_analyzers()
  chdir("#{ENV['URA_PROJECT']}/bin") do 
    sh 'scram b -j 4'
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
  if not (File.directory? output_name)
    sh "mkdir -p #{output_name}"
  end
  toy_dirs = /toy_\d+/
  Dir["#{input_name}/*"].each do |path|
    if toy_dirs =~ path
      next
    end
    if File.directory? path
      bname = File.basename(path)
      newdir = "#{output_name}/#{bname}"
      publish_pics(path, newdir)
    elsif path.end_with? '.png'
      `cp #{path} #{output_name}/.`
    elsif path.end_with? '.raw_txt'
      `cp #{path} #{output_name}/.`
    end
  end
end
