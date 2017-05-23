Given "I start the debugger with the PHP script $script" do |script|
  vdebug.start_listening
  full_script_path = Dir.getwd + "/" + script
  run_php_script full_script_path
  vdebug.running?.should be(true), "Vdebug is not running: #{vdebug.messages}"
end
