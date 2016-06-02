tools = "#{$fwk_dir}/rake/tools.rb"
require tools

rule ".cfg" do |t|
  sh "touch #{t.name}"
  puts t.investigation
end

$external_opts=''
rule ".root" => [ 
    # The cfg
    proc {|targ| targ.sub(%r{results/.*/(.*)/.*root}, "\\1.cfg")},
    # The sample file list .txt file
    proc {|targ| targ.sub(%r{results/(.*)/.*/(.*).root}, "inputs/\\1/\\2.txt")} ] do |t|
  #delegate scram for checking if something needs to be built
  scram_build_analyzers()
  # Make the output directory
  sh "mkdir -p `dirname #{t.name}`"
  workers = ENV.fetch('URA_NTHREADS', 2)
  executable = File.basename(File.dirname(t.name))
  puts executable
  cfg = t.prerequisites[0]
  inputs = t.prerequisites[1]
  sh "time #{executable} #{inputs} #{t.name} -c  #{cfg} --threads #{workers} #{$external_opts}"
end

task :analyze, [:analyzer,:sample,:opts,:dirtag] do |t, args|
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

task :test, [:analyzer, :sample, :limit] do |t, args|
  bname = File.basename(args.analyzer).split('.')[0]
  jobid = ENV['jobid']
  samples = Dir.glob("inputs/#{jobid}/*.txt").map{|x| File.basename(x).split('.')[0]}
  if args.sample
    regex = /#{args.sample}/
    samples = samples.select{|x| x =~ regex}
  end

  limit=""
  if args.limit
    limit = "-l #{args.limit}"
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
  #delegate scram for checking if something needs to be built
  scram_build_analyzers()
  task :testThis => [] do |u|
    samples_to_test.each do |sample|
      input_list = "inputs/#{jobid}/#{sample}.txt"
      nlines =  %x{wc -l #{input_list}}.to_i
      sh "time #{bname} #{input_list} #{sample}.#{bname}.test.root -c #{bname}.cfg --threads 1 --J #{nlines} -v #{limit}"
    end
  end
  Rake::Task["testThis"].invoke
end

task :track_batch, [:submit_dir, :ignore_correctness] do |t, args|
  puts "running on #{ENV['HOST']}"
  addopt = ''
  holdopt = ''
  if args.ignore_correctness == 'True'
    addopt='--ignoreFailed '
  else
    holdopt = "--check_correctness #{args.submit_dir}"
  end
  sh "hold.py #{holdopt}"
  Dir.chdir(args.submit_dir) do
    sh "addjobs.py --fastHadd #{addopt}"
  end
  analyzer = File.basename(args.submit_dir).split(/BATCH_\d+_/)[1]
  target_dir = "results/#{ENV['jobid']}/#{analyzer}"
  sh "mkdir -p #{target_dir}"
  sh "cp #{args.submit_dir}/*.root #{target_dir}/."
  sh "echo #{args.submit_dir} > #{target_dir}/meta.info"
end

task :analyze_batch, [:analyzer,:samples,:opts] do |t, args|
  puts "running on #{ENV['HOST']}"
  bname = File.basename(args.analyzer).split('.')[0]
  jobid = ENV['jobid']

  samples = ''
  if args.samples
    samples="--samples='#{args.samples}'"
  end
  opts = ''
  if args.opts
    opts="--opts='#{args.opts}'"
  end
  if File.file?('splitting.json')
    opts+='--splitting=splitting.json'
  end

  #delegate scram for checking if something needs to be built
  scram_build_analyzers()
  task :runThisBatch => [] do |u|
    submit_dir = "/uscms_data/d3/#{ENV['USER']}/BATCH_#{Time.now.to_i}_#{bname}"
    puts "Submitting to #{submit_dir}"
    sh "jobsub.py #{submit_dir} #{bname} #{samples} #{opts}"
    Rake::Task["track_batch"].invoke(submit_dir)
  end
  Rake::Task["runThisBatch"].invoke
end
