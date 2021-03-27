all: pdf

pdf: readme.md
	pandoc readme.md -o readme.pdf\
		--template eisvogel -V book --top-level-division=chapter

watch:
	nix-shell -p entr --run "echo 'readme.md' | entr make"
