mkdir .plugin_temp
cp -r auxiliary/ .plugin_temp
cp -r dependencies/ .plugin_temp
cp -r parsers .plugin_temp
cp -r icons .plugin_temp

cp codehealth.py .plugin_temp
cp compare.py .plugin_temp
cp comment_parse.py .plugin_temp
cp '"Default (Linux).sublime-keymap"' .plugin_temp
cp '"Default (OSX).sublime-keymap"' .plugin_temp
cp '"Default (Windows).sublime-keymap"' .plugin_temp

cd .plugin_temp
zip -r ../CodeHealth.zip *
cd ..
rm -rf .plugin_temp
