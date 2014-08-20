#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import argparse
import math
import os
import sys
import xlrd

from svg import *

SHEET_NAME_INDEX = "index"

ATTRS_REGIONS  = ("title", "fill-color", "fg-color", "line-color", "size")
ATTRS_GENERICS = ("width", "height", "center-x", "center-y", "start-angle", "radius", "line-width", "line-positive-color", "line-negative-color", "region-radius", "region-is-log", "title-x", "title-y")
ATTRS_EXPERIMENTS = ("sheet-name", "output-name", "title")

row = lambda ws, r: map(lambda x: x.value, ws.row(r))
cell = lambda ws, r, c: ws.row(r)[c].value


def error(msg):
    sys.stderr.write("\n\n!!! ERROR: %s\n\n" % msg)
    sys.exit(1)


class Expression(object):
    def __init__(self):
        self._title = "<no title>"

    """
    Load the expression data from a given file.
    """
    def load(self, fname):
        if not os.path.isfile(fname):
            error("File '%s' not found." % fname)

        wb = xlrd.open_workbook(fname)
        self._load_index(wb)

        self._data = {}

        for (name, attrs) in self._experiments.items():
            sheet_name = attrs['sheet-name']

            if sheet_name in wb.sheet_names():
                self._data[name] = self._load_data(wb, sheet_name)
            else:
                error("Sheet '%s' not found in file '%s'." % (sheet_name, fname))

    def draw(self, dirname):
        for name in self._experiments.keys():
            sys.stdout.write("Drawing experiment '%s' into '%s' file...\n" % (name, dirname + os.sep + self._experiments[name]['output-name']))
            self._draw_experiment(name, dirname)
        sys.stdout.write("OK\n")

    def _draw_experiment(self, name, dirname):
        experiment = self._experiments[name]
        (names, values) = self._data[name]

        # draw SVG
        svg = SVG(height=self._generics['height'], width=self._generics['width'])
        g = Group(stroke="black", stroke_width=1)
        svg.add(g)

        # add title
        txt = Text(self._generics['title-x'], self._generics['title-y'], cdata=CData(experiment['title']))
        g.add(txt, order=2000)

        coords = {}

        for (i, namei) in enumerate(names):
            vi = values["%s.%s" % (namei, namei)]

            vi = (math.exp(vi) if self._generics['region-is-log'] else vi) * self._generics['region-radius']

            # compute each region's coordinates
            coords[namei] = state_coord(i, self._generics['start-angle'], 360/len(names)+1, self._generics['center-x'], self._generics['center-y'], self._generics['radius'])
            (cxi, cyi) = coords[namei]

            # Add one circle per region
            region = self._regions[namei]
            g.add(Circle(cxi, cyi, vi, region['line-color'], fill=region['fill-color']), order=1000)
            txt = Text(cxi, cyi+5, cdata=CData(region['title']))
            g.add(txt, order=2000)

            for (j, namej) in enumerate(names):
                if j >= i:
                    break

                (cxj, cyj) = coords[namej]
                vj = values["%s.%s" % (namei, namej)]

                #print k1, k2, v1, v2
                line_color = self._generics['line-positive-color'] if vj > 0 else self._generics['line-negative-color']

                g.add(Line(cxi, cyi, cxj, cyj, stroke=line_color, stroke_width=abs(vj) * self._generics['line-width']))

        svg.write_svg(dirname + os.sep + experiment['output-name'])
        return

    """
    Loads the information from the index sheet.
    """
    def _load_index(self, wb):
        ws = wb.sheet_by_name(SHEET_NAME_INDEX)

        self._regions = None
        self._generics = None
        self._experiments = None

        r = 0

        while r < ws.nrows:
            txt = cell(ws, r, 0)

            if txt == "regions":
                self._regions = self._load_index_table(ws, 'Regions', r, ATTRS_REGIONS)

            elif txt == "generics":
                self._generics = self._load_index_values(ws, 'Generics', r, ATTRS_GENERICS)

            elif txt == "experiments":
                self._experiments = self._load_index_table(ws, 'Experiments',  r, ATTRS_EXPERIMENTS)

            r += 1

        if self._regions is None:
            error("Missing group 'regions'.")

        if self._generics is None:
            error("Missing group 'generics'.")

        if self._experiments is None:
            error("Missing group 'experiments'.")

    def _load_index_table(self, ws, name, r, attrs):
        ret = {}

        header = row(ws, r)
        attr_cols = {}

        for attr in attrs:
            if attr in header:
                attr_cols[attr] = header.index(attr)
            else:
                error("Missing column '%s' in sheet 'index', group '%s'." % (attr, name))

        i = r+1
        while (i < ws.nrows) and (cell(ws, i, 0) != ""):
            data = row(ws, i)

            gname = data[0]

            ret[gname] = {'name': gname}

            for (attr, col) in attr_cols.items():
                ret[gname][attr] = data[col]

            i += 1

        return ret

    def _load_index_values(self, ws, name, r, attrs):
        ret = {}
        attr_cols = {}

        i = r+1
        while (i < ws.nrows) and (cell(ws, i, 0) != ""):
            attr_cols[cell(ws, i, 0)] = i
            i += 1

        for attr in attrs:
            if attr in attr_cols.keys():
                ret[attr] = cell(ws, attr_cols[attr], 1)
            else:
                error("Missing row '%s' in sheet 'index', table '%s'." % (attr, name))

        return ret

    def _load_data(self, wb, sheet_name):
        names = []
        values = {}

        ws = wb.sheet_by_name(sheet_name)

        nrows = ws.nrows
        ncols = len(row(ws, 0))

        for r in xrange(1, nrows):
            rname = cell(ws, r, 0)
            names.append(rname)

            if rname not in self._regions.keys():
                error("Region '%s' was found in sheet '%s' row '%d' but was not defined in 'index' sheet." % (rname, sheet_name, r))

            for c in xrange(r, ncols):
                cname = cell(ws, 0, c)

                if cname not in self._regions.keys():
                    error("Region '%s' was found in the header of sheet '%s' but was not defined in 'index' sheet." % (cname, sheet_name))

                if (r == c) and (rname != cname):
                    error("Regions on row %d x col %d don't match '%s' != '%s'" % (r, c, rname, cname))

                # the values are simmetric
                values["%s.%s" % (rname, cname)] = cell(ws, r, c)
                values["%s.%s" % (cname, rname)] = cell(ws, r, c)

        return (names, values)


def state_coord(i, angle_start, angle_step, cx, cy, radius):
    angle = angle_start + angle_step * i

    x = radius * math.cos(math.radians(angle)) + cx
    y = radius * math.sin(math.radians(angle)) + cy

    return (x, y)

#
# MAIN
#

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file",  help="Excel file")
    args = parser.parse_args()

    if not os.path.isfile(args.file):
        error("File '%s' not found." % args.file)

    exp = Expression()
    exp.load(args.file)
    exp.draw(os.path.dirname(args.file))
    quit()
