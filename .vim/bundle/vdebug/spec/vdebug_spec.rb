require 'spec_helper'
require_relative "../rubylib/vdebug"

describe Vdebug do
  before do
    @vimserver = double("vimserver")
    @vim = double("vim", server: @vimserver)
    @vdebug = Vdebug.new vim
  end

  after do
    @vdebug.remove_lock_file!
  end

  let(:vimrunner) { @vim }
  let(:vdebug) { @vdebug }

  describe "when it starts listening" do
    context "calling start_listening" do

      it "should send the command to start vdebug" do
        vim.server.should_receive(:remote_send).
          with(":python debugger.run()<CR>")
        vdebug.start_listening
      end
    end

  end

  describe "the debugger commands" do
    context "step over" do
      it "should send the command to vdebug" do
        vim.should_receive(:command).
          with('python debugger.step_over()')
        vdebug.step_over
      end
    end
  end

  describe "the status queries" do
    context "asking whether it's connected" do
      it "should query the vdebug api" do
        vim.should_receive(:command).
          with("python print debugger.runner.is_alive()").
          and_return("True")
        vdebug.connected?
      end

      context "when the vdebug api returns 'False'" do
        before do
          vim.should_receive(:command).and_return("False")
        end
        subject { vdebug.connected? }
        it { should be false }
      end

      context "when the vdebug api returns 'True'" do
        before do
          vim.should_receive(:command).and_return("True")
        end
        subject { vdebug.connected? }
        it { should be true }
      end
    end
  end

  describe "the buffer detection" do
    context "from a vim string containing a no name buffer" do
      before do
        vim.should_receive(:command).and_return <<-BUF
      1  a   "[No Name]"                    line 1
        BUF
      end

      context "calling buffer names" do
        subject { vdebug.buffers }

        its(:length) { should == 1 }
        it { should == { 1 => "[No Name]" } }
      end

      context "checking whether the gui is open" do
        subject { vdebug.gui_open? }

        it { should be false }
      end
    end

    context "from a vim string containing vdebug buffers names" do
      before do
        vim.should_receive(:command).and_return <<-BUF
      1  a   "[No Name]"                    line 1
      2 %a   "~/.vim/bundle/vdebug/tmpspace/test.php" line 2
      3  a   "DebuggerWatch"                line 0
      4  a   "DebuggerStack"                line 0
      5  a   "DebuggerStatus"               line 0
        BUF
      end

      context "calling buffer names" do
        subject { vdebug.buffers }

        its(:length) { should == 5 }
        it {
          should == {
            1 => "[No Name]",
            2 => "~/.vim/bundle/vdebug/tmpspace/test.php",
            3 => "DebuggerWatch",
            4 => "DebuggerStack",
            5 => "DebuggerStatus"
          }
        }

      end

      context "checking whether the gui is open" do
        subject { vdebug.gui_open? }

        it { should be true }
      end
    end
  end

  describe "the buffer retrieval" do
    context "getting the watch window content" do
      let(:buffer) { <<-BUF
This is a buffer
Multiple lines
Other things
        BUF
      }

      context "when the watch buffer exists" do
        before do
          vdebug.should_receive(:buffers).and_return({
            3 => 'DebuggerWatch'
          })
          vim.should_receive(:echo).
            with('join(getbufline(3, 1, "$"), "\n")').
            and_return(buffer)
        end

        subject { vdebug.watch_window_content }
        it { should == buffer }
      end

      context "when the watch buffer doesn't exist" do
        before do
          vdebug.should_receive(:buffers).and_return({
            1 => '[No Name]'
          })
        end

        it "should raise a BufferNotFound error" do
          expect { vdebug.watch_window_content }.to raise_error Vdebug::BufferNotFound
        end
      end
    end

    context "getting the status window content" do
      let(:buffer) { <<-BUF
This is a the status window
Etc.
        BUF
      }

      context "when the status buffer exists" do
        before do
          vdebug.should_receive(:buffers).and_return({
            6 => 'DebuggerStatus'
          })
          vim.should_receive(:echo).
            with('join(getbufline(6, 1, "$"), "\n")').
            and_return(buffer)
        end

        subject { vdebug.status_window_content }
        it { should == buffer }
      end

      context "when the status buffer doesn't exist" do
        before do
          vdebug.should_receive(:buffers).and_return({
            1 => '[No Name]'
          })
        end

        it "should raise a BufferNotFound error" do
          expect { vdebug.status_window_content }.to raise_error Vdebug::BufferNotFound
        end
      end
    end
  end
end
