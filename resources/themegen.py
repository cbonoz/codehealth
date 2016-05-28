"""
file: themegen.py
generates the scheme theme settings to be added for the different health background color highlights
"""
import math
# <dict>
#     <key>name</key>
#     <string>String</string>
#     <key>scope</key>
#     <string>string</string>
#     <key>settings</key>
#     <dict>
#         <key>foreground</key>
#         <string>#E6DB74</string>
#     </dict>
# </dict>


def get_health_color(val):
    if val<0:
        val = 0
    elif val>100:
        val = 100
        
    hue = math.floor((100 - val) * 120 / 100);  # go from green to red
    saturation =abs(val - 50)/50;   # fade to white as it approaches 50
    return (hue,saturation,val)

def element_string(index,color):
    return """<dict>
        <key>name</key>
        <string>Color_"""+ str(index) + """</string>
        <key>scope</key>
        <string>color_""" + str(index) + """</string>
        <key>settings</key>
        <dict>
            <key>background</key>
            <string>""" + str(color) + """</string>
        </dict>
    </dict>"""

def percent_to_rgb(percent):
    percent = 100 - percent
    if (percent == 100):
        percent = 99
    
    r,g,b,a=0,0,0,96

    if (percent < 50):
        #green to yellow
        r = math.floor(255 * (percent / 50))
        g = 255

    else:
        #yellow to red
        r = 255
        g = math.floor(255 * ((50 - percent % 50) / 50))
    
    # res = struct.pack('BBB',*rgb).encode('hex')
    return '#%02x%02x%02x%02x' % (r,g,b,a)
    # return "rgb(" + str(r) + "," + str(g) + "," + str(b) + ")";

for i in range(100,-1,-1):
    color = percent_to_rgb(i)
    s = element_string(i,color)
    print(s)
