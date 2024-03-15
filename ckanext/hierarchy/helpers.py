import ckan.plugins as p
import ckan.model as model
from ckan.common import request
from ckan.lib.helpers import helper_functions as h


def group_tree(organizations=[], type_='organization'):
    full_tree_list = p.toolkit.get_action('group_tree')({}, {'type': type_})

    if not organizations:
        return full_tree_list
    else:
        filtered_tree_list = group_tree_filter(organizations, full_tree_list)
        return filtered_tree_list


def group_tree_filter(organizations, group_tree_list, highlight=False):
    # this method leaves only the sections of the tree corresponding to the
    # list since it was developed for the users, all children organizations
    # from the organizations in the list are included
    def traverse_select_highlighted(group_tree, selection=[], highlight=False):
        # add highlighted branches to the filtered tree
        if group_tree['highlighted']:
            # add to the selection and remove highlighting if necessary
            if highlight:
                selection += [group_tree]
            else:
                selection += group_tree_highlight([], [group_tree])
        else:
            # check if there is any highlighted child tree
            for child in group_tree.get('children', []):
                traverse_select_highlighted(child, selection)

    filtered_tree = []
    # first highlights all the organizations from the list in the three
    for group in group_tree_highlight(organizations, group_tree_list):
        traverse_select_highlighted(group, filtered_tree, highlight)

    return filtered_tree


def group_tree_section(id_, type_='organization', include_parents=True,
                       include_siblings=True):
    return p.toolkit.get_action('group_tree_section')(
        {'include_parents': include_parents,
         'include_siblings': include_siblings},
        {'id': id_, 'type': type_, })


def group_tree_parents(id_, type_='organization'):
    tree_node = p.toolkit.get_action('organization_show')({}, {'id': id_})
    if (tree_node['groups']):
        parent_id = tree_node['groups'][0]['name']
        parent_node = \
            p.toolkit.get_action('organization_show')({}, {'id': parent_id})
        return group_tree_parents(parent_id) + [parent_node]
    else:
        return []


def group_tree_get_longname(id_, default="", type_='organization'):
    if type_ == 'organization':
        tree_node = p.toolkit.get_action('organization_show')({}, {'id': id_})
    else:
        tree_node = p.toolkit.get_action('group_show')({}, {'id': id_})
    longname = tree_node.get("longname", default)
    if not longname:
        return default
    return longname


def group_tree_highlight(organizations, group_tree_list):
    def traverse_highlight(group_tree, name_list):
        if group_tree.get('name', "") in name_list:
            group_tree['highlighted'] = True
        else:
            group_tree['highlighted'] = False

    selected_names = [o.get('name', None) for o in organizations]

    for group in group_tree_list:
        traverse_highlight(group, selected_names)
    return group_tree_list


def get_allowable_parent_groups(group_id, _type='organization'):
    if group_id:
        group = model.Group.get(group_id)
        allowable_parent_groups = \
            group.groups_allowed_to_be_its_parent(type=_type)
    else:
        allowable_parent_groups = model.Group.all(
            group_type=_type)
    return allowable_parent_groups


def is_include_children_selected(fields):
    include_children_selected = False
    if request.params.get('include_children'):
        include_children_selected = True
    return include_children_selected


def render_tree(top_nodes=None, group_type='organization'):
    '''Returns HTML for a hierarchy of all publishers'''
    if not top_nodes:
        from ckan.logic import get_action
        from ckan import model
        context = {'model': model, 'session': model.Session}
        top_nodes = get_action('group_tree')(context=context,
                data_dict={'type': group_type})
        

    return _render_tree(top_nodes, group_type)


def render_tree_list(top_nodes=None, group_type='organization'):
    '''Returns HTML for a hierarchy of all publishers'''
    if not top_nodes:
        return ''
    return _render_tree(top_nodes, group_type)


def _render_tree(top_nodes, group_type):
    '''Renders a tree of nodes. 10x faster than Jinja/organization_tree.html
    Note: avoids the slow url_for routine.
    '''
    html = '<ul class="hierarchy-tree-top">'
    for node in top_nodes:
        html += _render_tree_node(node, group_type)
    return html + '</ul>'

def _render_tree_node(node, group_type):
    body = ''
    node_name = node['name']
    if node['highlighted']:
        body += f'<li class="highlighted" id="node_{node_name}">'
    else:
        body += f'<li id="node_{node_name}">'

    if group_type == "organization":
        url_with_name = h.url_for(u'{}.read'.format(group_type), id=node['name'])
        body += '<a href="%s">%s</a>' % (url_with_name, node['title'])
    else:
        url_with_name = h.url_for(u'{}.read'.format(group_type), id=node['name'])
        body += '<a href="%s">%s</a>' % (url_with_name, node['title'])
    if node['children']:
        body+= '<ul class="hierarchy-tree">'
        for child in node['children']:
            body += _render_tree_node(child, group_type)
        body += '</ul>'
    body += "</li>"
    return body



def package_themes_list(groups):
    group_rel_dict = {}

    for group in groups:
        group_id = group.get("id")

        if group_id not in group_rel_dict:
            group_dict = group_tree_section(id_=group_id, type_= "group")
            parent_id = group_dict.get("id")

            if parent_id in group_rel_dict:
                parent_data = group_rel_dict[parent_id].get("data")
                child_dict = [ch for ch in parent_data.get("children") if ch.get("id")== group_id]
                child_dict[0]['highlighted'] = True

            else:
                id = group_id if group_id == parent_id else parent_id
                group_rel_dict[id] = {
                    "data": group_dict,
                    "child": [ch.get("id") for ch in group_dict["children"]]
                }
        else:
            higlighted = group_rel_dict[group_id]["data"].get("higlighted")
            if not higlighted:
                highlighted = True

    group_list = []
    for _, values in group_rel_dict.items():
        group_list.append(values.get('data'))

    return group_list
                    

            
            