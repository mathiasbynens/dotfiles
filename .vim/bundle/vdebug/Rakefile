require 'rspec/core/rake_task'
require 'cucumber'
require 'cucumber/rake/task'

task :travis do
  system("export DISPLAY=:99.0 && bundle exec rake test:all")
  raise "Tests failed!" unless $?.exitstatus == 0
end

namespace :test do
  desc "Run all tests (unit and integration/specs)"
  task :all do
    puts "Running unit tests"
    Rake::Task["test:unit"].execute
    puts "Running integration (spec) tests"
    Rake::Task[:spec].execute
    puts "Running cucumber features"
    Rake::Task[:features].execute
  end

  desc "Run unit tests"
  task :unit do
    cmd = "python vdebugtests.py"
    puts cmd
    system cmd
  end

  desc "Run integration tests (alias for `spec`)"
  task :integration do
    Rake::Task[:spec]
  end
end

RSpec::Core::RakeTask.new(:spec)
Cucumber::Rake::Task.new(:features) do |t|
  t.cucumber_opts = "features --format pretty"
end

task :default => "test:all"
