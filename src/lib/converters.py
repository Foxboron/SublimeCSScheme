import cssutils
import plistlib


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
    sheet.add(info % (name, uuid))

    #settings
    l = []
    for k, v in a['settings'][0]['settings'].iteritems():
        st = "%s: %s;" % (str(k), str(v))
        l.append(st)
    p = ''.join(l)
    setting = "settings {%s}" % p
    sheet.add(setting)

    for i in a['settings']:
        if len(i.keys()) != 1:
            title = "%s#%s" % (i['name'], i['scope'])
            ss = []
            for k, v in i['settings'].iteritems():
                s = "%s: %s;" % (k, v)
                ss.append(s)
            css_defs = ''.join(ss)
            together = "%s {%s}" % (title, css_defs)
            sheet.add(together)
    return sheet.cssText