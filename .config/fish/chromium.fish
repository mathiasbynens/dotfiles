function deps --description "run gclient sync"
    env GYP_DEFINES=disable_nacl=1 gclient sync --jobs=70
end

function hooks --description "run gclient runhooks"
    env GYP_DEFINES=disable_nacl=1 gclient runhooks
end

function b --description "build chromium"
	set -l dir (grealpath $PWD/(git rev-parse --show-cdup)out/Default/)
	# 1000 will die with 'fatal: posix_spawn: No such file or directory'. 900 never has.

    set -l cmd "ninja -C "$dir" -j900 -l 48 chrome"  # rvm'd blink_tests
    echo "  > $cmd"
    eval $cmd
    echo ""
    echo "✅ Chrome build complete!  🕵️‍  Finishing blink_tests in the background..."
    eval "ninja -C $dir -j900 -l 48 blink_tests &"
    jobs
end

function cr --description "open built chromium (accepts runtime flags)"
    set -l dir (git rev-parse --show-cdup)/out/Default
    set -l cmd "./$dir/Chromium.app/Contents/MacOS/Chromium $argv"
    echo "  > $cmd"
    eval $cmd
end


function bcr --description "build chromium, then open it"
    if b
        cr
    end
end



function depsb --description "deps, then build chromium, then open it"
    if deps
        # #     if [ "$argv[1]" = "--skipgoma" ] ...
        gom
        b
    end
end

function depsbcr --description "deps, then build chromium, then open it"
    if deps
        # #     if [ "$argv[1]" = "--skipgoma" ] ...
        gom
        bcr
    end
end

function hooksbcr --description "run hooks, then build chromium, then open it"
    if hooks
        gom
        bcr
    end
end

function gom --description "run goma setup"
    set -x GOMAMAILTO /dev/null
    set -x GOMA_OAUTH2_CONFIG_FILE $HOME/.goma_oauth2_config
    set -x GOMA_ENABLE_REMOTE_LINK yes

    if not test (curl -X POST --silent http://127.0.0.1:8088/api/accountz)
        echo "Goma isn't running. Starting it."
        ~/goma/goma_ctl.py ensure_start
        return 0
    end

    set -l local_goma_version (curl -X POST --silent http://127.0.0.1:8088/api/taskz | jq '.goma_version[0]')
    set -l remote_goma_version (~/goma/goma_ctl.py latest_version | ack 'VERSION=(\d+)' | ack -o '\d+')

    if test local_goma_version = remote_goma_version
        echo 'Goma is running and up to date, continuing.'
    else
        echo 'Goma needs an update. Stopping and restarting.'
        ~/goma/goma_ctl.py stop
        ~/goma/goma_ctl.py ensure_start
    end
end
