task :getfiles, [:inputdir] do |t, args|
  jobid = ENV['jobid']
  sh "mkdir -p inputs/#{jobid}"
  Dir.glob("#{args.inputdir}/*").each do |dir|
    sample = File.basename(dir)
    sh "find #{dir} -name *.root | grep -v 'failed' > inputs/#{jobid}/#{sample}.txt"
  end
end

rule '.meta.json' => [proc {|trgt| trgt.sub(/\.meta\.json$/, '.txt')}] do |t|
  sample = File.basename(t.source).split('.')[0]
  workers = ENV.fetch('URA_NTHREADS', 1)
  mc = '--mc-mode'
  if sample.start_with? 'data'
    mc = ''
  end
  sh "compute_meta.py #{t.source} #{t.name} #{mc} --threads #{workers} --quiet"
end

task :getmeta => Dir.glob("#{ENV['URA_PROJECT']}/inputs/#{ENV['jobid']}/*.txt").map{|x| x.sub('.txt','.meta.json')}

rule '.lumi' => '.meta.json' do |t|
  sample = File.basename(t.source).split('.')[0]
  if sample.start_with? 'data'
    sh "json_extract.py #{t.source} #{t.source.sub(/\.meta\.json$/, '.run.json')} lumimap"
    puts "WARNING data lumi and PU distribution still to be computed"    
  else
    sh "get_mc_lumi.py #{t.source} #{ENV['URA_PROJECT']}/samples.json > #{t.name}"
  end  
end

task :getlumi => Dir.glob("#{ENV['URA_PROJECT']}/inputs/#{ENV['jobid']}/*.txt").map{|x| x.sub('.txt','.lumi')}

task :proxy do |t|
  jobid = ENV['jobid']
  samples = Dir.glob("inputs/#{jobid}/*.txt").map{|x| File.basename(x).split('.')[0]}
  mc_samples = samples.select{|x| not x.start_with?('data')}
  tfile = File.new(mc_samples[0], 'r').gets
  sh "make_tree_proxy.py #{tfile} Events"
end
