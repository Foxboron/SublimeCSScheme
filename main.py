import sublime, sublime_plugin
import src.lib.converters
#css2plist, plist2css

class CssXmlCommand(sublime_plugin.TextCommand, sublime.View):
    def run(self, edit):
        text = self.view.substr(sublime.Region(0, self.view.size()))
        l = src.lib.converters.css2plist(text)
        edit = self.view.begin_edit()
        self.view.replace(edit, sublime.Region(0, self.view.size()), l)
        self.view.end_edit(edit)

        

class XmlCssCommand(sublime_plugin.TextCommand, sublime.View):
    def run(self, edit):
        text = self.view.substr(sublime.Region(0, self.view.size()))
        l = src.lib.converters.plist2css(text)
        edit = self.view.begin_edit()
        self.view.replace(edit, sublime.Region(0, self.view.size()), l)
        self.view.end_edit(edit)


