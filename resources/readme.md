

CodeHealth Project
===

Original Authors
---

Chris Buonocore
Victor Kwan


Prototype Design
---

*A one-pager for the programming language design you will be prototyping in your project. This can be an entirely new design, or one of the designs that you presented in class. Either way, you must have a *concrete design*, not just a nebulous idea of what you want to do -- the latter will make it really difficult for you to do a good job on the project. So even if you're exploring an "old" design, you'll probably want to revise the original one-pager to make it more concrete.*


Motivation
---

##### What design questions will this project seek to answer?

1. Comment maintenance is often a secondary priority when it comes to making code changes. We want to be able to visualize how often comments go stale in codebases.
2. How can we better enforce programmer's updates to comments when the definition of the underlying code has changed?
3. Will developers find the health scores useful in terms of understanding what comments are new and up-to-date and what could potentially be stale (or no longer valid)?
4. How feasible is it to create a somewhat language-agnostic platform for analyzing comment health scores?
5. How feasible is it to create an accurate comment health scoring model (that runs in reasonable time)?

#####  What is the plan of attack, i.e., how does the codehealth system go about finding answers to the questions listed above?


1. Construct a source code parser that will lookup the commit history of the current file you are viewing
2. Extract the comments from the file into Comment Objects. Track these comments through the git history.
3. Build an algorithm that computes each comments' health score based on the metrics defined in the original one pager.
4. Build a light IDE plugin that will highlight comments according to their health rating (invoked via an IDE command)

Notes
---


##### Implementing CodeHealth Webhook Check
1. Pre-commit (client side)
  *  Checks to see if the comments of affected functions are updated.
  *  Looks at previous commit, looks at changes and editing.
  *  Warns user via command line of potential stale comments resulting from the latest changes
  *  This would be managed locally as part of the repo. There would be an npm module that invokes a script each time a local user attempts to create a new commit.
  * Would use a package like: https://github.com/observing/pre-commit


2. Pre-push (server side)
  * Requires hosting a server in which responds to events and dev
  * Push requests would be routed to the live server. Configuration guide here: https://developer.github.com/webhooks/configuring/
  * Server-side scripts would execute on the committed code. To push successfully, these scripts would need to pass.


##### My Opinion

Would recommend running the comment health test in a pre-commit-hook as the change would already be recorded when attempting to push. Push and pull only exchange information about already recorded changes. If a push test fails,  that user would still have "broken" revision in his or her repository (regardless of whether that person was able to successfully push to the server or not).

The workflow would require the npm package for pre-commit hooks. When the user invokes git commit via the command line, the pre-commit check would intervene and make sure the tests associated with the check pass.

https://github.com/SublimeText/WordHighlight


##### Implementation details:
Sublime Plugin requires editing the sublime color theme file (color themes for highlights are drawn from the user settings - defaults are used if this is not customly set). 
  * Will need to create/edit new color themes (red/orange/green) for health ratings for comments.
    Adding sublime plugin files to packages folder. Tools -> Developer -> Plugins will show you where the plugins folder is. If you add a .py sublime-style plugin file to this, it will automatically be loaded and begin executing.

Refer to https://www.sublimetext.com/docs/3/api_reference.html.

<!-- 

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
"""  -->

