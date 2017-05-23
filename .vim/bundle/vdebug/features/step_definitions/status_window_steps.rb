Then "the status should be $status" do |status|
  vdebug.status.should == status
end

Then "the status window should contain $string" do |string|
  vdebug.status_window_content.should include string
end
