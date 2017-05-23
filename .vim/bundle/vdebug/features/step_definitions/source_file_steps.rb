Given "I have a file $file containing" do |file, content|
  dir = File.dirname(file)
  unless dir == '.'
    FileUtils.mkdir_p(dir)
  end
  File.open file, "w" do |f|
    f.write content
  end
end
