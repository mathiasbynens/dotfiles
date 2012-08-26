# -*- coding: utf-8 -*-
'''notes.py

Used to highlight user-defined "annotations" such as TODO, README, etc.,
depending user choice.
'''

import sublime

from base_linter import BaseLinter

CONFIG = {
    'language': 'Annotations'
}


class Linter(BaseLinter):
    DEFAULT_NOTES = ["TODO", "README", "FIXME"]

    def built_in_check(self, view, code, filename):
        annotations = self.select_annotations(view)
        regions = []

        for annotation in annotations:
            regions.extend(self.find_all(code, annotation, view))

        return regions

    def select_annotations(self, view):
        '''selects the list of annotations to use'''
        return view.settings().get("annotations", self.DEFAULT_NOTES)

    def extract_annotations(self, code, view, filename):
        '''extract all lines with annotations'''
        annotations = self.select_annotations(view)
        annotation_starts = []

        for annotation in annotations:
            start = 0
            length = len(annotation)

            while True:
                start = code.find(annotation, start)

                if start != -1:
                    end = start + length
                    annotation_starts.append(start)
                    start = end
                else:
                    break

        regions_with_notes = set([])

        for point in annotation_starts:
            regions_with_notes.add(view.extract_scope(point))

        regions_with_notes = sorted(list(regions_with_notes))
        text = []

        for region in regions_with_notes:
            row, col = view.rowcol(region.begin())
            text.append("[{0}:{1}]".format(filename, row + 1))
            text.append(view.substr(region))

        return '\n'.join(text)

    def find_all(self, text, string, view):
        ''' finds all occurences of "string" in "text" and notes their positions
            as a sublime Region
        '''
        found = []
        length = len(string)
        start = 0

        while True:
            start = text.find(string, start)

            if start != -1:
                end = start + length
                found.append(sublime.Region(start, end))
                start = end
            else:
                break

        return found
