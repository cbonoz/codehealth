import sublime, sublime_plugin
import json

class ClearChangesCommand(sublime_plugin.EventListener):
    def on_post_save_async(self, view):
        view.erase_regions('unsaved')
        sublime.status_message("HighlightUnsaved: No Unsaved Changes")

class HighlightUnsavedCommand(sublime_plugin.EventListener):
    def on_modified(self, view):
        #this works for selecting line
        # n=14
        # row_point = view.text_point(14, 0) #get the n + 1th row
        # unsaved = view.get_regions('unsaved') + [view.line(s) for s in [sublime.Region(row_point)]
        unsaved = view.get_regions('unsaved') + [view.line(s) for s in view.sel()]

        sublime.status_message(str(unsaved))
        view.add_regions("unsaved", unsaved, "unsaved", "dot", sublime.HIDDEN | sublime.PERSISTENT)


        """
        should follow the style of this page:
        https://github.com/SublimeLinter/SublimeLinter3/blob/3f2973811f1fbb38568677be7be7bfbe77f7f4f4/lint/highlight.py


        sublime.DRAW_EMPTY. Draw empty regions with a vertical bar. By default, they aren't drawn at all.
        sublime.HIDE_ON_MINIMAP. Don't show the regions on the minimap.
        sublime.DRAW_EMPTY_AS_OVERWRITE. Draw empty regions with a horizontal bar instead of a vertical one.
        sublime.DRAW_NO_FILL. Disable filling the regions, leaving only the outline.
        sublime.DRAW_NO_OUTLINE. Disable drawing the outline of the regions.
        sublime.DRAW_SOLID_UNDERLINE. Draw a solid underline below the regions.
        sublime.DRAW_STIPPLED_UNDERLINE. Draw a stippled underline below the regions.
        sublime.DRAW_SQUIGGLY_UNDERLINE. Draw a squiggly underline below the regions.
        sublime.PERSISTENT. Save the regions in the session.
        sublime.HIDDEN. Don't draw the regions.
        """ 