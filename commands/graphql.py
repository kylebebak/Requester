import sublime
import sublime_plugin

import re
from threading import Thread

import requests
try:
    from graphql.parser import GraphQLParser
except ImportError:
    GraphQLParser = None

from ..core import RequestCommandMixin
from ..core.parsers import parse_requests
from ..core.responses import prepare_request


introspection_query = """
query IntrospectionQuery {
  __schema {
    queryType { name }
    mutationType { name }
    subscriptionType { name }
    types {
      ...FullType
    }
    directives {
      name
      description
      locations
      args {
        ...InputValue
      }
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
    deprecationReason
  }
  inputFields {
    ...InputValue
  }
  interfaces {
    ...TypeRef
  }
  enumValues(includeDeprecated: true) {
    name
    description
    isDeprecated
    deprecationReason
  }
  possibleTypes {
    ...TypeRef
  }
}

fragment InputValue on __InputValue {
  name
  description
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
    """If request was to a GQL endpoint, send introspection query and set response
    on view.
    """
    if not req.skwargs.get('gql') or GraphQLParser is None:
        return

    def _set(view, url):
        kwargs = dict(req.kwargs)
        kwargs.pop('params', None)
        kwargs.pop('json', None)
        response = requests.get(url, params={'query': introspection_query}, **kwargs)
        view.settings().set('requester.gql_schema', response.json())

    thread = Thread(target=lambda: _set(view, req.url.split('?')[0]))
    thread.start()


class RequesterGqlAutocompleteListener(sublime_plugin.ViewEventListener):
    def on_modified(self):
        schema = self.view.settings().get('requester.gql_schema', None)
        if not schema:
            return
        content = self.view.substr(sublime.Region(0, self.view.size()))
        m = re.search(r'\bgql\s*=\s*("|\')+', content)
        if m is None:
            return

        offset, pos = m.end(), self.view.sel()[0].begin()

        try:
            request = parse_requests(content, n=1)[0]

            if getattr(self.view, '_env', None) is None:
                self.view._env = RequestCommandMixin.get_env_dict_from_string(
                   self.view.settings().get('requester.env_string', None)
                )
            req = prepare_request(request, self.view._env, 1)
            gql = req.skwargs['gql']
        except Exception as e:
            print('GraphQL Error: {}'.format(e))
            return

        print(gql, gql[pos-offset])
