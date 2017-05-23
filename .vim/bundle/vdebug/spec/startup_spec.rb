require 'spec_helper'
require 'socket'

describe "startup" do
  context "starting the debugger" do
    before { vim.server.remote_send ':python debugger.run()<CR>' }

    # Try and connect via tcp socket
    it "should create a tcp server socket" do
      expect { TCPSocket.new('localhost', 9000).close }.not_to raise_error
    end

    after  { vim.command 'python debugger.close()' }
  end
end
