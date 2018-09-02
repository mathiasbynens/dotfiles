function header {
    echo ""
    echo "================================================="
    echo ""
    echo "$1"
    echo ""
    echo "================================================="
    echo ""
}

function footer {
    echo ""
    echo "DONE"
    echo ""
    echo "-------------------------------------------------"
    echo ""
}

function install {
  cmd=$1
  shift
  for pkg in "$@";
  do
   # ignore comments
   if [[ $pkg == \#* ]]; then
    continue
   fi

   if brew list -1 | grep -q "^${pkg}\$"; then
     echo "Package '$pkg' is installed"
     continue
   fi

   if $cmd $pkg; then
    echo "Installed $pkg"
   else
    echo "Failed to install $pkg"
   fi
  done
}

function uninstall {
  cmd=$1
  shift
  for pkg in "$@";
  do
   if $cmd $pkg; then
    echo "Uninstalled $pkg"
   else
    echo "Failed to uninstall $pkg"
   fi
  done
}


function dotfile {
  shift
  for pkg in "$@";
  do
   if $pkg; then
    echo "Uninstalled $pkg"
   else
    echo "Failed to uninstall $pkg"
   fi
  done
}
