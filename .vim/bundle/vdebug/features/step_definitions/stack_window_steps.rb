Then "the first item on the stack should show the file $file" do |file|
  vdebug.stack.first[:file].should include file
end

Then "the first item on the stack should show line $line" do |line|
  vdebug.stack.first[:line].should == line
end

Then "item $item on the stack should show the file $file" do |idx, file|
  idx = idx.to_i
  stack_length = vdebug.stack.length
  stack_length.should be >= idx, "There are only #{stack_length} items on the stack"
  vdebug.stack[idx-1][:file].should include file
end

Then "item $item on the stack should show line $line" do |idx, line|
  idx = idx.to_i
  stack_length = vdebug.stack.length
  stack_length.should be >= idx, "There are only #{stack_length} items on the stack"
  vdebug.stack[idx-1][:line].should == line
end
