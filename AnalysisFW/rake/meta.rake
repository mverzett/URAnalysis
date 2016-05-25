task :getfiles, [:inputdir] do |t, args|
  jobid = ENV['jobid']
  sh "mkdir -p inputs/#{jobid}"
  Dir.glob("#{args.inputdir}/#{jobid}/*").each do |dir|
    sample = File.basename(dir)
    files = `find #{dir} -name '*.root' | grep -v 'failed'` # avoid issues with empty samples causing crashes
    if files.empty?
      puts "sample #{sample} has not files! Skipping..."
    else
      File.open("inputs/#{jobid}/#{sample}.txt", 'w') do |file|
        file << files
      end
    end
  end
  sh "sed -i 's|/eos/uscms/|root://cmseos.fnal.gov//|g' inputs/#{jobid}/*.txt"
end

rule '.meta.json' => [proc {|trgt| trgt.sub(/\.meta\.json$/, '.txt')}] do |t|
  sample = File.basename(t.source).split('.')[0]
  workers = ENV.fetch('URA_NTHREADS', 1)
  mc = '--mc-mode'
  if sample.start_with? 'data'
    mc = ''
  end
  sh "compute_meta.py #{t.source} #{t.name} #{mc} --thread #{workers} --quiet"
end

task :getmeta => Dir.glob("#{ENV['URA_PROJECT']}/inputs/#{ENV['jobid']}/*.txt").map{|x| x.sub('.txt','.meta.json')}

#
# Meta on batch for every sample
#
task :track_meta_batch, [:submit_dir] do |t, args|
  puts "running on #{ENV['HOST']}"
  sh "hold.py --check_correctness #{args.submit_dir} --outtype=json"
  Dir.chdir(args.submit_dir) do
    content = Dir["*"]
    content.each do |dir|
      puts dir
      if not File.directory?(dir) 
        next
      end
      if not dir.start_with?('data') 
        sh "hadd -f -O #{dir}.meta.pu.root #{dir}/*.root"
      end      
      sh "merge_meta_jsons.py #{dir}.meta.json #{dir}/*.json"
    end
  end
  target_dir = "inputs/#{ENV['jobid']}"
  sh "cp #{args.submit_dir}/*.root #{target_dir}/."
  sh "cp #{args.submit_dir}/*.json #{target_dir}/."
  sh "mkdir -p #{target_dir}/INPUT/."
  sh "cp #{args.submit_dir}/*.root #{target_dir}/INPUT/."
end

task :meta_batch, [:sample] do |t, args|
  puts "running on #{ENV['HOST']}"
  jobid = ENV['jobid']

  opts = "--splitting=20 --nocfg --notransfer --noconversion --samples=#{args.sample}"

  submit_dir = "/uscms_data/d3/#{ENV['USER']}/BATCH_#{Time.now.to_i}_meta"
  puts "Submitting to #{submit_dir}"
  sh "jobsub.py #{submit_dir} compute_meta.py #{opts}"
  Rake::Task["track_meta_batch"].invoke(submit_dir)
end

rule '.lumi' => '.meta.json' do |t|
  sample = File.basename(t.source).split('.')[0]
  if sample.start_with? 'data'
    sh "json_extract.py #{t.source} #{t.source.sub(/\.meta\.json$/, '.run.json')} lumimap"
    puts "WARNING data lumi and PU distribution still to be computed"    
  else
    sh "get_mc_lumi.py #{t.source} #{ENV['URA_PROJECT']}/samples.json > #{t.name}"
  end  
end

multitask :getlumi => Dir.glob("#{ENV['URA_PROJECT']}/inputs/#{ENV['jobid']}/*.txt").map{|x| x.sub('.txt','.lumi')} do |t|
  sh "mkdir -p inputs/#{ENV['jobid']}/INPUT"
  sh "cp inputs/#{ENV['jobid']}/*.meta.pu*.root inputs/#{ENV['jobid']}/INPUT/."
end

task :proxy, [:sample] do |t, args|
  jobid = ENV['jobid']
  samples = Dir.glob("inputs/#{jobid}/*.txt").map{|x| File.basename(x).split('.')[0]}
  mc_samples = samples.select{|x| not x.start_with?('data')}
  if not args.sample.empty?
    regex = Regexp.new args.sample
    mc_samples = mc_samples.select{|x| regex =~ x}
  end
  tfile = File.new("inputs/#{jobid}/"+mc_samples[0]+".txt", 'r').gets.strip
  sh "make_tree_proxy.py --nodict #{tfile} Events"
end
