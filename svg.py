#!/usr/bin/env python

colorstr = lambda r, g, b: "#%02x%02x%02x" % (r, g, b)


class Tag(object):

    def __init__(self, name):
        self.name = name
        self.prefix = ""
        self.attrs = []
        self.children = []

    def add(self, tag, order=0):
        self.children.append((tag, order))

    def set(self, name, value):
        self.attrs.append((name, value))

    def cdata(self, cdata):
        self.cdata = cdata

    def xml(self, indent=0):
        attrs_str = ""
        child_str = ""

        attrs_str = " ".join(map(lambda a: " %s=\"%s\"" % (a[0], a[1]), filter(lambda a: not a[1] is None, self.attrs)))

        #for (name, value) in self.attrs:
        #    if not value is None:
        #        attrs_str += " %s=\"%s\"" % (name, str(value))

        self.children.sort(key=lambda c:c[1])

        for (child, order) in self.children:
            child_str += child.xml(indent+1)

        indent_str = "\t" * indent

        if(child_str == ""):
            result = self.prefix + "%s<%s %s/>\n" % (indent_str, self.name, attrs_str)
        else:
            result = self.prefix + "%s<%s %s>\n%s%s</%s>\n" % (indent_str, self.name, attrs_str, child_str, indent_str, self.name)

        return(result)

    def write_svg(self, filename):
        if(not filename.endswith(".svg")):
            filename += ".svg"

        file = open(filename, 'w')
        file.writelines(self.xml())
        file.close()


class CData(object):

    def __init__(self, cdata):
        self.cdata = cdata

    def xml(self, indent=0):
        return "%s%s\n" % ("\t" * indent, self.cdata)


class SVG(Tag):

    def __init__(self, height=400, width=400):
        super(SVG, self).__init__("svg")

        self.prefix = '<?xml version="1.0"?>'

        self.set("xmlns:dc", "http://purl.org/dc/elements/1.1/")
        self.set("xmlns:cc", "http://web.resource.org/cc/")
        self.set("xmlns:rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
        self.set("xmlns:svg", "http://www.w3.org/2000/svg")
        self.set("xmlns", "http://www.w3.org/2000/svg")

        self.set("height", height)
        self.set("width", width)


class DrawableTag(Tag):

    def __init__(self, name, stroke=None, stroke_width=None):
        super(DrawableTag, self).__init__(name)

        self.set("stroke", stroke)
        self.set("stroke-width", stroke_width)


class FillableTag(DrawableTag):
    def __init__(self, name, stroke=None, stroke_width=None, fill=None):
        super(FillableTag, self).__init__(name, stroke=stroke, stroke_width=stroke_width)

        self.set("fill", fill)


class Group(DrawableTag):

    def __init__(self, stroke=None, stroke_width=None, fill_opacity="1"):
        super(Group, self).__init__("g", stroke=stroke, stroke_width=stroke_width)

        self.set("fill-opacity", fill_opacity)


class Line(DrawableTag):

    def __init__(self, x1, y1, x2, y2, stroke=None, stroke_width=None):
        super(Line, self).__init__("line", stroke=stroke, stroke_width=stroke_width)

        self.set("x1", x1)
        self.set("y1", y1)
        self.set("x2", x2)
        self.set("y2", y2)


class Circle(FillableTag):

    def __init__(self, cx, cy, r, stroke=None, stroke_width=None, fill="white"):
        super(Circle, self).__init__("circle", stroke=stroke, stroke_width=stroke_width, fill=fill)

        self.set("cx", cx)
        self.set("cy", cy)
        self.set("r", r)


class Rectangle(FillableTag):

    def __init__(self, x, y, width, height, r, stroke=None, stroke_width=None, fill="white"):
        super(Rectangle, self).__init__("rect", stroke=stroke, stroke_width=stroke_width, fill=fill)

        self.set("x", x)
        self.set("y", y)
        self.set("height", height)
        self.set("width", width)


class Text(DrawableTag):

    def __init__(self, x, y, cdata, stroke=None, stroke_width=None, font_size=24, font_weight="normal", font_family="Arial"):
        super(Text, self).__init__("text", stroke=stroke, stroke_width=stroke_width)

        self.set("x", x)
        self.set("y", y)
        self.set("font-size", font_size)
        self.set("font-weight", font_weight)
        self.set("font-family", font_family)

        self.set("text-anchor", "middle")
        self.set("dominant-baseline", "central")

        self.add(cdata)


def test():
    svg = SVG()
    g = Group(stroke="black", stroke_width=1)
    svg.add(g)

    g.add(Rectangle(100, 100, 200, 200, colorstr(0, 255, 255)))
    g.add(Line(200, 200, 200, 300, stroke_width=5))
    g.add(Line(200, 200, 300, 200, stroke_width=5))
    g.add(Line(200, 200, 100, 200, stroke_width=5))
    g.add(Line(200, 200, 200, 100, stroke_width=5))
    g.add(Circle(200, 200, 30, colorstr(0, 0, 255), fill=colorstr(0, 0, 255)))
    g.add(Circle(200, 300, 30, colorstr(0, 255, 0), fill=colorstr(0, 255, 0)))
    g.add(Circle(300, 200, 30, colorstr(255, 0, 0), fill=colorstr(255, 0, 0)))
    g.add(Circle(100, 200, 30, colorstr(255, 255, 0), fill=colorstr(255, 255, 0)))
    g.add(Circle(200, 100, 30, colorstr(255, 0, 255), fill=colorstr(255, 0, 255)))

    g.add(Circle(50, 50, 5, colorstr(255, 0, 255), fill=colorstr(255, 0, 255)))

    txt = Text(50, 55, cdata=CData("Text"))

    g.add(txt)

    svg.write_svg('test')

if __name__ == '__main__':
    test()
