When "I evaluate $expression" do |expr|
  vdebug.evaluate expr
  vdebug.running?.should be(true), "Vdebug is not running: #{vdebug.messages}"
end
