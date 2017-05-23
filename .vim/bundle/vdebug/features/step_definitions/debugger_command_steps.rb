When "I step over" do
  vdebug.step_over
  vdebug.running?.should be(true), "Vdebug is not running: #{vdebug.messages}"
end

When "I step in" do
  vdebug.step_in
  vdebug.running?.should be(true), "Vdebug is not running: #{vdebug.messages}"
end
