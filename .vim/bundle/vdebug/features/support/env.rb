require 'vimrunner'
require 'securerandom'
require_relative "../../rubylib/vdebug"

begin
  TMP_DIR = "tmpspace_#{SecureRandom::hex(3)}"
  PHP_INI = File.expand_path('../../../.travis.php.ini', __FILE__)

  Before do
    Dir.mkdir TMP_DIR unless Dir.exists? TMP_DIR
    Dir.chdir TMP_DIR

    # Setup plugin in the Vim instance
    plugin_path = File.expand_path('../../..', __FILE__)
    vim.add_plugin(plugin_path, 'plugin/vdebug.vim')
  end

  After do
    kill_vim
    Dir.chdir '..'
    system "rm -r #{TMP_DIR}"
  end

rescue Exception
  system "rm -r #{TMP_DIR}"
  raise
end
