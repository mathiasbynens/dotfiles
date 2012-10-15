SCRIPT=$(wildcard plugin/*.vim)
AUTOL =$(wildcard autoload/*.vim)
DOC=$(wildcard doc/*.txt)
PLUGIN=$(shell basename "$$PWD")
VERSION=$(shell sed -n '/Version:/{s/^.*\(\S\.\S\+\)$$/\1/;p}' $(SCRIPT))

.PHONY: $(PLUGIN).vba README

all: uninstall vimball install README

vimball: $(PLUGIN).vba

clean:
	rm -f *.vba */*.orig *.~* .VimballRecord

dist-clean: clean

install:
	vim -N -c':so %' -c':q!' $(PLUGIN)-$(VERSION).vba

uninstall:
	vim -N -c':RmVimball' -c':q!' $(PLUGIN)-$(VERSION).vba

undo:
	for i in */*.orig; do mv -f "$$i" "$${i%.*}"; done

README:
	cp -f $(DOC) README

$(PLUGIN).vba:
	rm -f $(PLUGIN)-$(VERSION).vba
	vim -N -c 'ru! vimballPlugin.vim' -c ':call append("0", [ "$(SCRIPT)", "$(AUTOL)", "$(DOC)"])' -c '$$d' -c ":%MkVimball $(PLUGIN)-$(VERSION)  ." -c':q!'
	ln -f $(PLUGIN)-$(VERSION).vba $(PLUGIN).vba
     
release: version all

version:
	perl -i.orig -pne 'if (/Version:/) {s/\.(\d*)/sprintf(".%d", 1+$$1)/e}' ${SCRIPT} ${AUTOL}
	perl -i -pne 'if (/GetLatestVimScripts:/) {s/(\d+)\s+:AutoInstall:/sprintf("%d :AutoInstall:", 1+$$1)/e}' ${SCRIPT}  ${AUTOL}
	#perl -i -pne 'if (/Last Change:/) {s/\d+\.\d+\.\d\+$$/sprintf("%s", `date -R`)/e}' ${SCRIPT}
	perl -i -pne 'if (/Last Change:/) {s/(:\s+).*\n/sprintf(": %s", `date -R`)/e}' ${SCRIPT} ${AUTOL}
	perl -i.orig -pne 'if (/Version:/) {s/\.(\d+).*\n/sprintf(".%d %s", 1+$$1, `date -R`)/e}' ${DOC}
	VERSION=$(shell sed -n '/Version:/{s/^.*\(\S\.\S\+\)$$/\1/;p}' $(SCRIPT))
