Then "the watch window should show $text" do |text|
  vdebug.watch_window_content.should include text
end

Then "the watch window variable $var should be $value" do |var, value|
  vdebug.watch_vars[var].should == value
end
