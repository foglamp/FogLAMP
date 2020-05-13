# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = python3 -msphinx
SPHINXPROJ    = FogLAMP
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:	foglamp_plugins.rst
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile generated foglamp_plugins.rst plugin_configuration clean

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile 
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

generated: foglamp_plugins.rst plugin_configuration

foglamp_plugins.rst: 
	@echo Building page with table of plugins
	@bash scripts/foglamp_plugin_list foglamp_plugins.rst

plugin_configuration: 
	@echo Building plugin configuration appendices
	@bash scripts/plugin_documentation

clean:
	@rm -f foglamp_plugins.rst
	@rm -rf plugins
	@rm -rf "$(BUILDDIR)"
