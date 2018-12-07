class Node(object):
    def __str__(self):
        children = []
        for k, v in self.__dict__.items():
            if v:
                if isinstance(v, (list, tuple)):
                    v = '[%s]' % ', '.join([str(v) for v in v if v])
                children.append('%s=%s' % (k, v))
        return u'<%s%s%s>' % (
            self.__class__.__name__,
            ': ' if children else '',
            ', '.join(children),
        )

    __repr__ = __str__

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        for k, v in self.__dict__.items():
            if getattr(other, k) != v:
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)


class Document(Node):
    def __init__(self, definitions=None):
        self.definitions = definitions or []


class Definition(Node):
    pass


class FragmentDefinition(Definition):
    def __init__(self, name, type_condition, selections, directives=None):
        self.name = name
        self.type_condition = type_condition
        self.selections = selections
        self.directives = directives or []


class OperationDefinition(Definition):
    def __init__(self, selections, name, variable_definitions=None,
                 directives=None):
        self.selections = selections
        self.name = name
        self.variable_definitions = variable_definitions or []
        self.directives = directives or []


class Query(OperationDefinition):
    """
    In shorthand notation (when document contains only one query without
    variable definitions or directives) query can be anonymous.
    """
    def __init__(self, selections, name=None, variable_definitions=None,
                 directives=None):
        super(Query, self).__init__(
            selections=selections,
            name=name,
            variable_definitions=variable_definitions,
            directives=directives,
        )


class Mutation(OperationDefinition):
    pass


class Selection(Node):
    pass


class Field(Selection):
    def __init__(self, name, alias=None, arguments=None, directives=None,
                 selections=None):
        self.name = name
        self.alias = alias
        self.arguments = arguments or []
        self.directives = directives or []
        self.selections = selections or []


class FragmentSpread(Selection):
    def __init__(self, name, directives=None):
        self.name = name
        self.directives = directives or []


class InlineFragment(Selection):
    def __init__(self, type_condition, selections, directives=None):
        self.type_condition = type_condition
        self.selections = selections
        self.directives = directives or []


class Argument(Node):
    def __init__(self, name, value):
        self.name = name
        self.value = value


class Value(Node):
    def __init__(self, value):
        self.value = value


class VariableDefinition(Value):
    def __init__(self, name, type, default_value=None):
        self.name = name
        self.type = type
        self.default_value = default_value


class Variable(Value):
    def __init__(self, name):
        self.name = name


class Directive(Node):
    def __init__(self, name, arguments=None):
        self.name = name
        self.arguments = arguments or []


class Type(Node):
    pass


class NamedType(Type):
    def __init__(self, name):
        self.name = name


class ListType(Type):
    def __init__(self, type):
        self.type = type


class NonNullType(Type):
    def __init__(self, type):
        self.type = type


class TypeCondition(NamedType):
    pass
