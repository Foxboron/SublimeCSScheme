import cssutils
import plistlib
import logging


def css2plist(css):
    sheet = cssutils.parseString(css, validate=False)
    d = {}
    d['settings'] = []
    for rule in sheet:
        if rule.selectorText == "info":
            for i in rule.style:
                d[i.name] = i.value

        if "#" in rule.selectorText:
            l = {'settings': {}, 'name': '', 'scope': ''}
            r = rule.selectorText.split('#')
            l['name'], l['scope'] = r[0], r[1]
            for p in rule.style:
                l['settings'][p.name] = p.value
            d['settings'].append(l)

        if rule.selectorText == "settings":
            l = {'settings': {}}
            for p in rule.style:
                l['settings'][p.name] = p.value
            d['settings'].append(l)
    return plistlib.writePlistToString(d)
    

def plist2css(xml):
    a = plistlib.readPlistFromString(xml)
    cssutils.log.setLevel(logging.FATAL)
    sheet = cssutils.css.CSSStyleSheet(validating=None)

    #info
    info = "info {name: %s; uuid: %s}"
    name = a['name']
    uuid = a['uuid']
    cssadd(sheet, info % (name, uuid))

    #settings
    l = []
    for k, v in a['settings'][0]['settings'].iteritems():
        st = "%s: %s;" % (str(k), str(v))
        l.append(st)
    p = ''.join(l)
    setting = "settings {%s}" % p
    cssadd(sheet, setting)

    for i in a['settings']:
        if len(i.keys()) != 1:
            title = "%s#%s" % (i['name'], i['scope'])
            ss = []
            for k, v in i['settings'].iteritems():
                s = "%s: %s;" % (k, v)
                ss.append(s)
            css_defs = ''.join(ss)
            together = "%s {%s}" % (title, css_defs)
            cssadd(sheet, together)
    return sheet.cssText


def cssadd(sheet, rule):
    try:
        sheet.add(rule)
    except Exception, e:
        if "Unexpected CHAR" in e:
            print "You got a invalid letter!"
        elif "Unknown syntax or no value" in e:
            print "Empty tag in the XML!"
        elif "Unexpected NUMBER" in e or "No match in Choice" in e:
            print "Print wrong HEX value"
        raise "Error bro."
