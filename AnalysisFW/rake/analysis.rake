tools = "#{$fwk_dir}/rake/tools.rb"
require tools

rule ".exe" => [
    #the input .cc
    proc {|target| target.sub(%r{(ENV['URA_PROJECT']/)?bin/(.*).exe}, "#{ENV['URA_PROJECT']}/\\2.cc")},
    proc { "#{ENV['URA_PROJECT']}/lib/.lib_timestamp"},
    proc { "#{ENV['URA']}/AnalysisFW/lib/.lib_timestamp"}] do |t|
  puts t.investigation
  project_dir = ENV['URA_PROJECT']
  fwk_dir = ENV['URA']+'/AnalysisFW'
  local_libs = Dir.glob("#{project_dir}/lib/*.*o")
  fwk_libs = Dir.glob("#{fwk_dir}/lib/*.*o")
  prj_libs = Array[ENV.fetch('URA_PROJECT_LIBS', '')]
  
  local_includes = "#{project_dir}/interface/"
  fwk_includes = "#{fwk_dir}/interface/"
  
  sh compile_string([local_includes, fwk_includes],local_libs+fwk_libs+prj_libs, t.prerequisites[0], t.name)
  #"g++ -I#{local_includes} -I#{fwk_includes} `root-config --cflags` `root-config --libs` -lboost_program_options #{libs} #{t.prerequisites[0]} -o #{t.name}"
end

rule ".cfg" do |t|
  sh "touch #{t.name}"
  puts t.investigation
end

$external_opts=''
rule ".root" => [ 
    # The analyzer executable
    proc {|targ| targ.sub(%r{results/.*/(.*)/.*root}, "bin/\\1.exe")},
    # The cfg
    proc {|targ| targ.sub(%r{results/.*/(.*)/.*root}, "\\1.cfg")},
    # The sample file list .txt file
    proc {|targ| targ.sub(%r{results/(.*)/.*/(.*).root}, "inputs/\\1/\\2.txt")} ] do |t|
  # Make the output directory
  sh "mkdir -p `dirname #{t.name}`"
  workers = ENV.fetch('URA_NTHREADS', 2)
  executable = File.basename(t.prerequisites[0])
  cfg = t.prerequisites[1]
  inputs = t.prerequisites[2]
  sh "time #{executable} #{inputs} #{t.name} -c  #{cfg} --threads #{workers} #{$external_opts}"
end

task :analyze, [:analyzer,:sample,:opts] do |t, args|
  bname = File.basename(args.analyzer).split('.')[0]
  jobid = ENV['jobid']
  samples = Dir.glob("inputs/#{jobid}/*.txt").map{|x| File.basename(x).split('.')[0]}
  if args.sample
    regex = /#{args.sample}/
    samples = samples.select{|x| x =~ regex}
  end
  if args.opts
    $external_opts=args.opts
  end
  #remove meta tag if any
  sh "rm -f results/#{jobid}/#{bname}/meta.info"
  rootfiles = samples.map{|x| "results/#{jobid}/#{bname}/#{x}.root"}
  task :runThis => rootfiles
  Rake::Task["runThis"].invoke
  if args.opts
    $external_opts=''
  end
end

task :analyze_only, [:analyzer, :sample] do |t, args|
  bname = File.basename(args.analyzer).split('.')[0]
  jobid = ENV['jobid']
  samples = Dir.glob("inputs/#{jobid}/#{args.sample}.txt").map{|x| File.basename(x).split('.')[0]}
  rootfiles = samples.map{|x| "results/#{jobid}/#{bname}/#{x}.root"}
  task :runThis => rootfiles
  Rake::Task["runThis"].invoke
end

task :test, [:analyzer, :sample] do |t, args|
  bname = File.basename(args.analyzer).split('.')[0]
  jobid = ENV['jobid']
  samples = Dir.glob("inputs/#{jobid}/*.txt").map{|x| File.basename(x).split('.')[0]}
  if args.sample
    regex = /#{args.sample}/
    samples = samples.select{|x| x =~ regex}
  end
  data_samples = samples.select{|x| x.start_with?('data')}
  mc_samples = samples.select{|x| not x.start_with?('data')}
  samples_to_test = []
  if not data_samples.empty?
    samples_to_test << data_samples[0]
  end
  if not mc_samples.empty?
    samples_to_test << mc_samples[0]
  end
  jobid = ENV['jobid']
  task :testThis => "bin/#{bname}.exe" do |u|
    samples_to_test.each do |sample|
      input_list = "inputs/#{jobid}/#{sample}.txt"
      nlines =  %x{wc -l #{input_list}}.to_i
      sh "time #{bname}.exe #{input_list} #{sample}.#{bname}.test.root -c #{bname}.cfg --threads 1 --J #{nlines} -v"
    end
  end
  Rake::Task["testThis"].invoke
end

task :track_batch, [:submit_dir] do |t, args|
  sh "hold.py --check_correctness #{args.submit_dir}"
  Dir.chdir(args.submit_dir) do
    sh 'addjobs.py'
  end
  analyzer = File.basename(args.submit_dir).split(/BATCH_\d+_/)[1]
  target_dir = "results/#{ENV['jobid']}/#{analyzer}"
  sh "mkdir -p #{target_dir}"
  sh "cp #{args.submit_dir}/*.root #{target_dir}/."
  sh "echo #{args.submit_dir} > #{target_dir}/meta.info"
end

task :analyze_batch, [:analyzer,:samples,:opts] do |t, args|
  bname = File.basename(args.analyzer).split('.')[0]
  jobid = ENV['jobid']

  samples = ''
  if args.samples
    samples="--samples=#{args.samples}"
  end
  opts = ''
  if args.opts
    opts="--opts='#{args.opts}'"
  end
  if File.file?('splitting.json')
    opts+='--splitting=splitting.json'
  end

  task :runThisBatch => "bin/#{bname}.exe" do |u|
    submit_dir = "/uscms_data/d3/#{ENV['USER']}/BATCH_#{Time.now.to_i}_#{bname}"
    puts "Submitting to #{submit_dir}"
    sh "jobsub #{submit_dir} #{bname}.exe #{samples} #{opts}"
    Rake::Task["track_batch"].invoke(submit_dir)
  end
  Rake::Task["runThisBatch"].invoke
end
