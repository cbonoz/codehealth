
# import sublime, sublime_plugin

# class ExampleCommand(sublime_plugin.TextCommand):
#     def run(self, edit):
#         self.view.insert(edit, 0, "Hello, World!")

# import sublime, sublime_plugin
# import json, subprocess

# class ClearChangesCommand(sublime_plugin.EventListener):
#     def on_post_save_async(self, view):
#         view.erase_regions('unsaved')
#         sublime.status_message("HighlightUnsaved: No Unsaved Changes")

# class HighlightUnsavedCommand(sublime_plugin.EventListener):
#     def on_modified(self, view):
#         #this works for selecting line
#         # n=14
#         # row_point = view.text_point(14, 0) #get the n + 1th row
#         # unsaved = view.get_regions('unsaved') + [view.line(s) for s in [sublime.Region(row_point)]
#         unsaved = view.get_regions('unsaved') + [view.line(s) for s in view.sel()]

#         sublime.status_message(str(unsaved))
#         view.add_regions("unsaved", unsaved, "unsaved", "dot", sublime.HIDDEN | sublime.PERSISTENT)

