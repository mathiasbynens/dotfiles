function setup
    cd $HOME
    for file in $HOME/.config/fish/functions/fish_*.fish;
        rm $file
    end
    echo 'function fish_prompt; end' > $HOME/.config/fish/functions/fish_prompt.fish
    rm --recursive --force $HOME/.config/fish/functions/theme-pure
    echo '' > $HOME/.config/fish/config.fish
end

function teardown
    rm --force $HOME/.config/fish/functions/fish_prompt.fish
    echo 'function fish_prompt; end' > $HOME/.config/fish/functions/fish_prompt.fish
end

if test $USER = 'nemo'
    @test "installation methods: manually" (
        curl git.io/pure-fish --output /tmp/pure_installer.fish --location --silent >/dev/null
        and source /tmp/pure_installer.fish

        rm --recursive --force $HOME/.config/fish/functions/theme-pure        
        and install_pure >/dev/null

        fish -c 'fish_prompt | grep -c "❯"' 
    ) = 1
end

if test $USER = 'nemo'
    @test "installation methods: with fisher" (
        fisher add rafaelrinaldi/pure >/dev/null
        fish -c 'fish_prompt | grep -c "❯"' 
    ) = 1
end

if test $USER = 'nemo'
    @test "installation methods: with OMF (Oh-My-Fish!)" (
        rm --recursive --force $HOME/.local/share/omf $HOME/.config/omf/

        curl -L https://get.oh-my.fish > install
        and fish install --noninteractive >/dev/null
        and fish -c "omf install pure; fish_prompt" | grep -c '❯' 
    ) = 1
end

# if test $USER = 'nemo'
#     @test "installation methods: with Fundle" (
#         rm --recursive --force $HOME/.config/fish/fundle/
#         mkdir --parents $HOME/.config/fish/functions
#         curl https://git.io/fundle --output $HOME/.config/fish/functions/fundle.fish --location --silent >/dev/null

#         fundle plugin rafaelrinaldi/pure >/dev/null
#         fundle install >/dev/null
#         cp $HOME/.config/fish/fundle/rafaelrinaldi/pure/{,functions/}fish_prompt.fish

#         fish -c 'fish_prompt | grep -c "❯"' 
#     ) = 1
# end
