require 'shellwords'

module VdebugHelper
  def vdebug
    @vdebug ||= Vdebug.new vim
  end

  def vim
    @vim ||= Vimrunner.start
  end

  def kill_vim
    if @vim
      @vim.kill
      @vim = nil
      if @vdebug
        @vdebug.remove_lock_file!
        @vdebug = nil
      end
    end
  end
end

module ScriptRunner
  STDERR_FILE = "error.out"

  def run_php_script(path)
    fork_and_run "php -c #{PHP_INI}", Shellwords.escape(path)
  end

  def stderr_contents
    File.read(STDERR_FILE)
  end

  def fork_and_run(bin, argstr)
    fork do
      exec %Q{XDEBUG_CONFIG="idekey=something" /usr/bin/env #{bin} #{argstr} 2>#{STDERR_FILE}}
      exit!
    end
    sleep 0.5
  end
end

World(VdebugHelper)
World(ScriptRunner)
