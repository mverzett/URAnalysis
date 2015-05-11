task :getfiles, [:inputdir] do |t, args|
  jobid = ENV['jobid']
  sh "mkdir -p inputs/#{jobid}"
  Dir.glob("#{args.inputdir}/*").each do |dir|
    sample = File.basename(dir)
    sh "ls #{dir}/*.root > inputs/#{jobid}/#{sample}.txt"
  end
end

rule '.meta.json' => [proc {|trgt| trgt.sub(/\.meta\.json$/, '.txt')}] do |t|
  sample = File.basename(t.source).split('.')[0]
  workers = ENV.fetch('URA_NTHREADS', 4)
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
    puts "WARNING data lumi and PU distribution still to be computed"
  else
    sh "get_mc_lumi.py #{t.source} #{ENV['URA_PROJECT']}/samples.json > #{t.name}"
  end  
end

task :getlumi => Dir.glob("#{ENV['URA_PROJECT']}/inputs/#{ENV['jobid']}/*.txt").map{|x| x.sub('.txt','.lumi')}
