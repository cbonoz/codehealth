Codehealth
=========

Codehealth is a Sublime Text 2/3 plugin that analyzes the health of code comments.

For now it supports **Git** version control

Install
-------

The easiest way to install is through **[Package Control](http://wbond.net/sublime\_packages/package\_control)**.

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

Features / Usage
----------------


Configuring
-----------

Open `Preferences -> Package Settings -> Codehealth -> Settings - Default` and look for available settings.

If you want to change something, don't do it in this file. Open `Preferences -> Package Settings -> Codehealth -> Settings - User` and put there your configuration.

You can configure is a type of icon (dot, circle or bookmark) and path for your VCS binaries (or leave them as is, if you have them in your PATH). It's also possible to set priority for VCS used (when you have more than one simultaneously) by reordering their definitions.

If some sacred punishment has been bestowed upon you, and you have no other choice but to use OS, where console has non-UTF8 encoding, you can set console_encoding parameter to the name of your beloved encoding. This parameter is specifically designed for Windows XP users, who have their git repositories in folders with cyrillic path. Since russian XP uses CP1251 as default encoding (including console), VCS diff commands will be encoded appropriately, when using this parameter.
ifferencing mechanism that may be specified for use in the user's runtime configuration.

### Line endings
Codehealth takes into account `default_line_ending` setting that you can change in your "User Settings" (or per project/file basis).  
It determines what characters to use to join lines when Codehealth does "Revert change" action.  
Valid values: `system` (OS-dependent), `windows` (CRLF) and `unix` (LF).

