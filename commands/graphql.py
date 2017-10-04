import sublime
import sublime_plugin

import re
import sys
import traceback
from threading import Thread
from collections import defaultdict

import requests
try:
    from graphql.parser import GraphQLParser
except ImportError:
    GraphQLParser = None

from ..core import RequestCommandMixin
from ..core.parsers import parse_requests
from ..core.responses import prepare_request


placeholder = '__introspection_placeholder'
introspection_query = """
query IntrospectionQuery {
  __schema {
    queryType { name }
    mutationType { name }
    subscriptionType { name }
    types {
      ...FullType
    }
  }
}

fragment FullType on __Type {
  kind
  name
  description
  fields(includeDeprecated: true) {
    name
    description
    args {
      ...InputValue
    }
    type {
      ...TypeRef
    }
    isDeprecated
  }
}

fragment InputValue on __InputValue {
  name
  type { ...TypeRef }
  defaultValue
}

fragment TypeRef on __Type {
  kind
  name
  ofType {
    kind
    name
    ofType {
      kind
      name
      ofType {
        kind
        name
        ofType {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
              }
            }
          }
        }
      }
    }
  }
}
"""


def set_graphql_on_view(view, req):
    """If request was to a GQL endpoint, send introspection query on a separate
    thread, parse response and set it on view.

    { name: [type, name, description] }
    """
    if GraphQLParser is None:
        print('Install graphql-py with pip for GraphQL autocomplete')
        return
    if not req.skwargs.get('gql'):
        return

    def _set(view, url):
        """Change list of types and sub list of fields on each type to dicts in
        which each type and subfield can be looked up by name.
        """
        kwargs = dict(req.kwargs)
        kwargs.pop('params', None)
        kwargs.pop('json', None)
        kwargs['timeout'] = 3
        response = requests.get(url, params={'query': introspection_query}, **kwargs)

        schema = response.json()['data']['__schema']  # get root `Query` type
        query_type = schema['queryType']['name']

        types = {}
        for t in schema['types']:
            types[t['name']] = t
            fields = {f['name']: f for f in (t['fields'] or [])}
            t['fields'] = fields

        view.settings().set('requester.gql_schema', (query_type, types))

    thread = Thread(target=lambda: _set(view, req.url.split('?')[0]))
    thread.start()


class RequesterGqlAutocompleteListener(sublime_plugin.ViewEventListener):
    def on_modified_async(self):
        schema = self.view.settings().get('requester.gql_schema', None)
        if not schema:
            return

        content = self.view.substr(sublime.Region(0, self.view.size()))
        m = re.search(r'\bgql\s*=\s*("|\')+', content)
        if m is None:
            return

        offset, idx = m.end(), self.view.sel()[0].begin()

        try:
            request = parse_requests(content, n=1)[0]

            if getattr(self.view, '_env', None) is None:
                self.view._env = RequestCommandMixin.get_env_dict_from_string(
                   self.view.settings().get('requester.env_string', None)
                )
            req = prepare_request(request, self.view._env, 1)
            gql = req.skwargs['gql']
            options = get_autocomplete_options(gql, idx-offset, schema)
            print(options)
        except:
            print('GraphQL Error:')
            traceback.print_exc(file=sys.stdout)
            return


def get_autocomplete_options(gql, idx, schema):
    """This method doesn't protect against exceptions. They should be handled by
    calling code.
    """
    start, end = slurp_word(gql, idx)
    if start == end:
        return []
    gql_parser = GraphQLParser()
    field = gql[start:end]
    ast = gql_parser.parse(gql[:start] + placeholder + gql[end:])

    for query in ast.definitions:  # get path if it exists
        path = placeholder_path(query, placeholder)
        if path is not None:
            break

    query_type, types = schema
    t = resolve_type(path, types, query_type)
    print(t)


def resolve_type(path, types, query_type):
    t = query_type
    for f in path[:-1]:  # stop before reaching placeholder
        field = types[t]['fields'][f]
        t = field['type']['name']
    return t


def placeholder_path(field, placeholder):
    """Not the most elegant implementation of DFS. It searches the whole tree and
    keeps track of the path to each node. If it finds `placeholder`, it saves this
    path and returns it after search is finished.
    """
    path = None

    def get_path(selection, placeholder, seen=None):
        seen = seen or []
        for sel in selection.selections:
            seen_ = list(seen)
            seen_.append(sel.name)
            if sel.name == placeholder:
                nonlocal path
                path = seen_
            get_path(sel, placeholder, seen_)

    get_path(field, placeholder)
    return path


def slurp_word(s, idx):
    """Return index boundaries of word adjacent to `idx` in `s`.
    """
    alnum = r'[A-Za-z0-9_]'
    try:
        start, end = idx, idx
        while True:
            if re.match(alnum, s[start-1]):
                start -= 1
            else:
                break
        end = idx
        while True:
            if re.match(alnum, s[end]):
                end += 1
            else:
                break
    except:
        return None, None
    else:
        return start, end
