from treemodel import Visitor
import re
from datetime import datetime

SELECTED='visitors.selected'

'''
When we explicitly match an item we want all it's descendants
matched unconditionally - even if they would have failed the match
we're running. The marked flag isn't enough since it's set by default
so we need another to represent the selection status just while we're
running a particular filter. We must remember to remove it when we're
done with a node or subsequent filters won't work properly
'''
class BaseFilterVisitor(Visitor):
    def __init__(self, include=True):
        self.include = include
    def begin_any (self, item):
        # inherit the SELECTED status
        if item.parent == None:
            item.attribs[SELECTED] = False
        else:
            item.attribs[SELECTED] = item.parent.attribs[SELECTED]
    def end_any (self, item):
        del item.attribs[SELECTED] # for the next filter
    def set_item_matched (self, item, matched):
        if not self.include:
            matched = not matched
        item.marked = matched
        item.attribs[SELECTED] = True
    def match_name (self, item, regexp):
        return re.search (regexp, item.name) != None
    def match_completed (self, item, regexp):
        if item.date_completed != None:
            # be careful - we want whole days, life gets confusing if we want to see
            # todays tasks but we also see some of yesterdays since it's <24hrs ago 
            days_elapsed = (datetime.today().date() - item.date_completed.date()).days
            date_str = item.date_completed.strftime ('%Y-%m-%d %A %B') + ' -' + str (days_elapsed) +'d'
        else:
            date_str = ''
        return re.search (regexp, date_str) != None

class FolderNameFilterVisitor(BaseFilterVisitor):
    def __init__(self, filtr, include=True):
        BaseFilterVisitor.__init__(self, include)
        self.filter = filtr
    def begin_folder (self, folder):
        if not folder.attribs[SELECTED] and self.filter != None:
            matched = self.match_name(folder, self.filter)
            self.set_item_matched(folder, matched);

class ProjectNameFilterVisitor(BaseFilterVisitor):
    def __init__(self, filtr, include=True):
        BaseFilterVisitor.__init__(self, include)
        self.filter = filtr
    def begin_project (self, project):
        if not project.attribs[SELECTED] and self.filter != None:
            matched = self.match_name(project, self.filter)
            self.set_item_matched(project, matched);

class ContextNameFilterVisitor(BaseFilterVisitor):
    def __init__(self, filtr, include=True):
        BaseFilterVisitor.__init__(self, include)
        self.filter = filtr
    def begin_context (self, context):
        if not context.attribs[SELECTED] and self.filter != None:
            matched = self.match_name(context, self.filter)
            self.set_item_matched(context, matched);
            
class TaskNameFilterVisitor(BaseFilterVisitor):
    def __init__(self, filtr, include=True):
        BaseFilterVisitor.__init__(self, include)
        self.filter = filtr
    def begin_task (self, project):
        if not project.attribs[SELECTED] and self.filter != None:
            matched = self.match_name(project, self.filter)
            self.set_item_matched(project, matched);
            
class ProjectCompletionFilterVisitor(BaseFilterVisitor):
    def __init__(self, filtr, include=True):
        BaseFilterVisitor.__init__(self, include)
        self.filter = filtr
    def begin_project (self, project):
        if not project.attribs[SELECTED] and self.filter != None:
            matched = self.match_completed(project, self.filter)
            self.set_item_matched(project, matched);

class TaskCompletionFilterVisitor(BaseFilterVisitor):
    def __init__(self, filtr, include=True):
        BaseFilterVisitor.__init__(self, include)
        self.filter = filtr
    def begin_task (self, task):
        if not task.attribs[SELECTED] and self.filter != None:
            matched = self.match_completed(task, self.filter)
            self.set_item_matched(task, matched);

class FlatteningVisitor (Visitor):
    def __init__(self):
        self.projects = []
    def begin_project (self, project):
        self.projects.append(project)
    def end_task (self, task):
        mypos = task.parent.children.index (task)
        for child in task.children:
            task.parent.children.insert (mypos, child)
            child.parent = task.parent
        task.children = []
        
class TaskCompletionSortingVisitor (Visitor):
    def end_project (self, project):
        project.children.sort(key=lambda item:self.get_key(item))
    def get_key (self, item):
        if item.date_completed != None:
            return item.date_completed
        return datetime.today()
    
class PruningFilterVisitor (Visitor):
    def end_project (self, project):
        self.prune_if_empty(project)
    def end_folder (self, folder):
        self.prune_if_empty(folder)
    def end_context (self, context):
        self.prune_if_empty(context)
    def prune_if_empty (self, item):
        if item.marked:
            empty = len ([x for x in item.children if x.marked]) == 0
            if empty:
                item.marked = False         