Codehealth
=========

**Codehealth** is a Sublime Text 2/3 plugin that analyzes the health of code comments.

in progress

How it Works
------------

The CodeHealth plugin calculates the health scores of the current file relative to the HEAD node in your remote git repository (need to have git configured to set your baseline).

CodeHealth runs a comparison of your currently-viewed file with the git repository HEAD version, so you have comment health scores that are calculated via a compare function: compare(current, HEAD). This returns a list of absolute comment healths, where the comments all originally started at 100 if current == HEAD. These healths are then color coded according to risk of decay.

Goal of this plugin is to encourage programmers to avoid comment decay and update comments regularly.

Package Setup
-------------

The easiest way to install CodeHealth is through **[Package Control](http://wbond.net/sublime\_packages/package\_control)**.

Once you install Package Control, restart ST3 and bring up the Command Palette (`Ctrl+Shift+P` on Linux/Windows, `Cmd+Shift+P` on OS X). Select "Package Control: Install Package", wait while Package Control fetches the latest package list, then select *Codehealth* when the list appears. The advantage of using this method is that Package Control will automatically keep *Codehealth* up to date with the latest version.

Or you can **download** the latest source from [GitHub](https://github.com/cbonoz/codehealth) and copy the *Codehealth* folder to your Sublime Text "Packages" directory.

Or **clone** the repository to your Sublime Text "Packages" directory:

    git clone git@github.com:cbonoz/codehealth.git


The "Packages" directory is located at:

* OS X:

        ~/Library/Application Support/Sublime Text 3/Packages/

* Linux:

        ~/.config/sublime-text-2/Packages/

* Windows:

        %APPDATA%/Roaming/Sublime Text 3/Packages/

<!-- Please, make sure your VCS (version control system) binaries is in the PATH (**especially if you are on Windows**).

To do that on Windows, open `Control Panel -> System -> Advanced system settings -> Environment variables -> System Variables`, find PATH, click "Edit" and append `;C:\path\to\VCS\binaries` for every VCS you will use (or make sure it's already there). -->

Installation
------------

### There are 3 methods for installing this plugin.

1. (Not set up yet) Search for "Code Health" via the "Package Control: Install Packages" menu. Note: If you don't have Sublime Package Control installed, you can find out how to install it here https://sublime.wbond.net/installation

2. Clone the repository into your Sublime Text 2/3 packages directory. `git clone git@github.com:cbonoz/codehealth.git

3. Download the .zip file and unzip it into your Sublime Text 2/3 packages directory. Note: You can find your Sublime Text 2/3 packages directory by going to Preferences > Browse Packages.

Directions for Manual Install
-----------------------------

1. Add **codehealth.py** to your Sublime Packages folder (ex: /Library/Application Support/Sublime Text 3/Packages/User/) as described above.
2. Insert contents of **codehealth.tmTheme** into your current Sublime theme file (usually located in the same folder as above). Your current selected theme can be found by going to Sublime Preferences and navigating to the checked option.

![Tooltip Light](http://s32.postimg.org/r33r55w3p/Screen_Shot_2016_05_19_at_10_22_33_PM.png)

3. Add the following commands to your User key bindings (can change commands if desired)

[
    { "keys": ["ctrl+alt+c"], "command": "activate_health" },
    { "keys": ["ctrl+alt+r"], "command": "remove_health" }
]


If the plugin is successfully activated, you should be able to toggle the comment health highlighting on/off via the activate_health and remove_health commands.

Should highlight similar to the below.

![Tooltip Light](http://s32.postimg.org/ywmfqyrb9/Screen_Shot_2016_05_19_at_10_12_35_PM.png)

Note the comment health highlight scores are indicated by color (also numerically for color-impaired). 

* **Red**: Bad Comment Health (highly likely to be outdated)
* **Orange**: Medium Health (possibly outdated)
* **Green**: Good Health (should be safe)

Features / Usage
----------------

1. Activate the Plugin by opening the Sublime command palette (via Command-Shift-P) and selecting *CommentHealth: Activate Health*

This will enable code health to be rendered and recalculated each save.

2. Deactivate the Plugin by opening the Sublime command palette (via Command-Shift-P) and selecting *CommentHealth: Remove Health*

Configuring
-----------

Open `Preferences -> Package Settings -> Codehealth -> Settings - Default` and look for available settings.

If you want to change something, don't do it in this file. Open `Preferences -> Package Settings -> CodeHealth -> Settings - User` and put there your configuration.

<!-- 
You can configure is a type of icon (dot, circle or bookmark) and path for your VCS binaries (or leave them as is, if you have them in your PATH). It's also possible to set priority for VCS used (when you have more than one simultaneously) by reordering their definitions.

If some sacred punishment has been bestowed upon you, and you have no other choice but to use OS, where console has non-UTF8 encoding, you can set console_encoding parameter to the name of your beloved encoding. This parameter is specifically designed for Windows XP users, who have their git repositories in folders with cyrillic path. Since russian XP uses CP1251 as default encoding (including console), VCS diff commands will be encoded appropriately, when using this parameter.
ifferencing mechanism that may be specified for use in the user's runtime configuration.
 -->
### Line endings
CodeHealth takes into account `default_line_ending` setting that you can change in your "User Settings" (or per project/file basis).  
It determines what characters to use to join lines when Codehealth does "Revert change" action.  
Valid values: `system` (OS-dependent), `windows` (CRLF) and `unix` (LF).

### Things to do:
* weighted radiation: more downward of comment than upward
* global radiation
* radiation calculation on save

### bugs
<!-- moving commment downwards affects  -->


