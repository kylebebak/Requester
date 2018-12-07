import ply.yacc as yacc

from .ast import *  # noqa
from .exceptions import SyntaxError
from .lexer import GraphQLLexer


class GraphQLParser(object):
    """
    GraphQL parser, builds AST.

    Can be used with any PLY-compatible lexer, by default uses GraphQLLexer.

    Usage example:

        parser = GraphQLParser()
        document = parser.parse(some_text)

    Use with custom lexer:

        parser = GraphQLParser()
        document = parser.parse(some_text, lexer=my_lexer)

    Note that custom lexer must provide the same set of tokens as defined in
    GraphQLLexer.tokens.

    """
    def __init__(self, debug=False, **kwargs):
        self.default_lexer = GraphQLLexer()
        self.tokens = self.default_lexer.tokens
        kwargs['debug'] = debug
        self.yacc = yacc.yacc(module=self, **kwargs)

    def parse(self, input=None, lexer=None, **kwargs):
        lexer = lexer or self.default_lexer
        return self.yacc.parse(input=input, lexer=lexer, **kwargs)

    start = 'document'

    def p_document(self, p):
        """
        document : definition_list
        """
        p[0] = Document(definitions=p[1])

    def p_document_shorthand(self, p):
        """
        document : selection_set
        """
        p[0] = Document(definitions=[Query(selections=p[1])])

    def p_document_shorthand_with_fragments(self, p):
        """
        document : selection_set fragment_list
        """
        p[0] = Document(definitions=[Query(selections=p[1])] + p[2])

    def p_fragment_list(self, p):
        """
        fragment_list : fragment_list fragment_definition
        """
        p[0] = p[1] + [p[2]]

    def p_fragment_list_single(self, p):
        """
        fragment_list : fragment_definition
        """
        p[0] = [p[1]]

    def p_definition_list(self, p):
        """
        definition_list : definition_list definition
        """
        p[0] = p[1] + [p[2]]

    def p_definition_list_single(self, p):
        """
        definition_list : definition
        """
        p[0] = [p[1]]

    def p_definition(self, p):
        """
        definition : operation_definition
                   | fragment_definition
        """
        p[0] = p[1]

    def operation_cls(self, operation_type):
        if operation_type == 'query':
            return Query
        elif operation_type == 'mutation':
            return Mutation

    def p_operation_definition1(self, p):
        """
        operation_definition : operation_type name variable_definitions directives selection_set
        """
        p[0] = self.operation_cls(p[1])(
            selections=p[5],
            name=p[2],
            variable_definitions=p[3],
            directives=p[4],
        )

    def p_operation_definition2(self, p):
        """
        operation_definition : operation_type name variable_definitions selection_set
        """
        p[0] = self.operation_cls(p[1])(
            selections=p[4],
            name=p[2],
            variable_definitions=p[3],
        )

    def p_operation_definition3(self, p):
        """
        operation_definition : operation_type name directives selection_set
        """
        p[0] = self.operation_cls(p[1])(
            selections=p[4],
            name=p[2],
            directives=p[3],
        )

    def p_operation_definition4(self, p):
        """
        operation_definition : operation_type name selection_set
        """
        p[0] = self.operation_cls(p[1])(selections=p[3], name=p[2])

    def p_operation_definition5(self, p):
        """
        operation_definition : operation_type variable_definitions directives selection_set
        """
        p[0] = self.operation_cls(p[1])(
            selections=p[4],
            variable_definitions=p[2],
            directives=p[3],
        )

    def p_operation_definition6(self, p):
        """
        operation_definition : operation_type variable_definitions selection_set
        """
        p[0] = self.operation_cls(p[1])(
            selections=p[3],
            variable_definitions=p[2],
        )

    def p_operation_definition7(self, p):
        """
        operation_definition : operation_type directives selection_set
        """
        p[0] = self.operation_cls(p[1])(
            selections=p[3],
            directives=p[2],
        )

    def p_operation_definition8(self, p):
        """
        operation_definition : operation_type selection_set
        """
        p[0] = self.operation_cls(p[1])(selections=p[2])

    def p_operation_type(self, p):
        """
        operation_type : QUERY
                       | MUTATION
        """
        p[0] = p[1]

    def p_selection_set(self, p):
        """
        selection_set : BRACE_L selection_list BRACE_R
        """
        p[0] = p[2]

    def p_selection_list(self, p):
        """
        selection_list : selection_list selection
        """
        p[0] = p[1] + [p[2]]

    def p_selection_list_single(self, p):
        """
        selection_list : selection
        """
        p[0] = [p[1]]

    def p_selection(self, p):
        """
        selection : field
                  | fragment_spread
                  | inline_fragment
        """
        p[0] = p[1]

    def p_field_all(self, p):
        """
        field : alias name arguments directives selection_set
        """
        p[0] = Field(name=p[2], alias=p[1], arguments=p[3], directives=p[4],
                     selections=p[5])

    def p_field_optional1_1(self, p):
        """
        field : name arguments directives selection_set
        """
        p[0] = Field(name=p[1], arguments=p[2], directives=p[3],
                     selections=p[5])

    def p_field_optional1_2(self, p):
        """
        field : alias name directives selection_set
        """
        p[0] = Field(name=p[2], alias=p[1], directives=p[3], selections=p[5])

    def p_field_optional1_3(self, p):
        """
        field : alias name arguments selection_set
        """
        p[0] = Field(name=p[2], alias=p[1], arguments=p[3], selections=p[4])

    def p_field_optional1_4(self, p):
        """
        field : alias name arguments directives
        """
        p[0] = Field(name=p[2], alias=p[1], arguments=p[3], directives=p[4])

    def p_field_optional2_1(self, p):
        """
        field : name directives selection_set
        """
        p[0] = Field(name=p[1], directives=p[2], selections=p[3])

    def p_field_optional2_2(self, p):
        """
        field : name arguments selection_set
        """
        p[0] = Field(name=p[1], arguments=p[2], selections=p[3])

    def p_field_optional2_3(self, p):
        """
        field : name arguments directives
        """
        p[0] = Field(name=p[1], arguments=p[2], directives=p[3])

    def p_field_optional2_4(self, p):
        """
        field : alias name selection_set
        """
        p[0] = Field(name=p[2], alias=p[1], selections=p[3])

    def p_field_optional2_5(self, p):
        """
        field : alias name directives
        """
        p[0] = Field(name=p[2], alias=p[1], directives=p[3])

    def p_field_optional2_6(self, p):
        """
        field : alias name arguments
        """
        p[0] = Field(name=p[2], alias=p[1], arguments=p[3])

    def p_field_optional3_1(self, p):
        """
        field : alias name
        """
        p[0] = Field(name=p[2], alias=p[1])

    def p_field_optional3_2(self, p):
        """
        field : name arguments
        """
        p[0] = Field(name=p[1], arguments=p[2])

    def p_field_optional3_3(self, p):
        """
        field : name directives
        """
        p[0] = Field(name=p[1], directives=p[2])

    def p_field_optional3_4(self, p):
        """
        field : name selection_set
        """
        p[0] = Field(name=p[1], selections=p[2])

    def p_field_optional4(self, p):
        """
        field : name
        """
        p[0] = Field(name=p[1])

    def p_fragment_spread1(self, p):
        """
        fragment_spread : SPREAD fragment_name directives
        """
        p[0] = FragmentSpread(name=p[2], directives=p[3])

    def p_fragment_spread2(self, p):
        """
        fragment_spread : SPREAD fragment_name
        """
        p[0] = FragmentSpread(name=p[2])

    def p_fragment_definition1(self, p):
        """
        fragment_definition : FRAGMENT fragment_name ON type_condition directives selection_set
        """
        p[0] = FragmentDefinition(name=p[2], type_condition=p[4],
                                  selections=p[6], directives=p[5])

    def p_fragment_definition2(self, p):
        """
        fragment_definition : FRAGMENT fragment_name ON type_condition selection_set
        """
        p[0] = FragmentDefinition(name=p[2], type_condition=p[4],
                                  selections=p[5])

    def p_inline_fragment1(self, p):
        """
        inline_fragment : SPREAD ON type_condition directives selection_set
        """
        p[0] = InlineFragment(type_condition=p[3], selections=p[5],
                              directives=p[4])

    def p_inline_fragment2(self, p):
        """
        inline_fragment : SPREAD ON type_condition selection_set
        """
        p[0] = InlineFragment(type_condition=p[3], selections=p[4])

    def p_fragment_name(self, p):
        """
        fragment_name : NAME
                      | FRAGMENT
                      | QUERY
                      | MUTATION
                      | TRUE
                      | FALSE
                      | NULL
        """
        p[0] = p[1]

    def p_type_condition(self, p):
        """
        type_condition : named_type
        """
        p[0] = p[1]

    def p_directives(self, p):
        """
        directives : directive_list
        """
        p[0] = p[1]

    def p_directive_list(self, p):
        """
        directive_list : directive_list directive
        """
        p[0] = p[1] + [p[2]]

    def p_directive_list_single(self, p):
        """
        directive_list : directive
        """
        p[0] = [p[1]]

    def p_directive(self, p):
        """
        directive : AT name arguments
                  | AT name
        """
        arguments = p[3] if len(p) == 4 else None
        p[0] = Directive(name=p[2], arguments=arguments)

    def p_arguments(self, p):
        """
        arguments : PAREN_L argument_list PAREN_R
        """
        p[0] = p[2]

    def p_argument_list(self, p):
        """
        argument_list : argument_list argument
        """
        p[0] = p[1] + [p[2]]

    def p_argument_list_single(self, p):
        """
        argument_list : argument
        """
        p[0] = [p[1]]

    def p_argument(self, p):
        """
        argument : name COLON value
        """
        p[0] = Argument(name=p[1], value=p[3])

    def p_variable_definitions(self, p):
        """
        variable_definitions : PAREN_L variable_definition_list PAREN_R
        """
        p[0] = p[2]

    def p_variable_definition_list(self, p):
        """
        variable_definition_list : variable_definition_list variable_definition
        """
        p[0] = p[1] + [p[2]]

    def p_variable_definition_list_single(self, p):
        """
        variable_definition_list : variable_definition
        """
        p[0] = [p[1]]

    def p_variable_definition1(self, p):
        """
        variable_definition : DOLLAR name COLON type default_value
        """
        p[0] = VariableDefinition(name=p[2], type=p[4], default_value=p[5])

    def p_variable_definition2(self, p):
        """
        variable_definition : DOLLAR name COLON type
        """
        p[0] = VariableDefinition(name=p[2], type=p[4])

    def p_variable(self, p):
        """
        variable : DOLLAR name
        """
        p[0] = Variable(name=p[2])

    def p_default_value(self, p):
        """
        default_value : EQUALS const_value
        """
        p[0] = p[2]

    def p_name(self, p):
        """
        name : NAME
             | FRAGMENT
             | QUERY
             | MUTATION
             | ON
             | TRUE
             | FALSE
             | NULL
        """
        p[0] = p[1]

    def p_alias(self, p):
        """
        alias : name COLON
        """
        p[0] = p[1]

    def p_value(self, p):
        """
        value : variable
              | INT_VALUE
              | FLOAT_VALUE
              | STRING_VALUE
              | null_value
              | boolean_value
              | enum_value
              | list_value
              | object_value
        """
        p[0] = p[1]

    def p_const_value(self, p):
        """
        const_value : INT_VALUE
                    | FLOAT_VALUE
                    | STRING_VALUE
                    | null_value
                    | boolean_value
                    | enum_value
                    | const_list_value
                    | const_object_value
        """
        p[0] = p[1]

    def p_boolean_value(self, p):
        """
        boolean_value : TRUE
                      | FALSE
        """
        p[0] = p[1]

    def p_null_value(self, p):
        """
        null_value : NULL
        """
        p[0] = p[1]

    def p_enum_value(self, p):
        """
        enum_value : NAME
                   | FRAGMENT
                   | QUERY
                   | MUTATION
                   | ON
        """
        p[0] = p[1]

    def p_list_value(self, p):
        """
        list_value : BRACKET_L value_list BRACKET_R
                   | BRACKET_L BRACKET_R
        """
        p[0] = p[2] if len(p) == 4 else []

    def p_value_list(self, p):
        """
        value_list : value_list value
        """
        p[0] = p[1] + [p[2]]

    def p_value_list_single(self, p):
        """
        value_list : value
        """
        p[0] = [p[1]]

    def p_const_list_value(self, p):
        """
        const_list_value : BRACKET_L const_value_list BRACKET_R
                         | BRACKET_L BRACKET_R
        """
        p[0] = p[2] if len(p) == 4 else []

    def p_const_value_list(self, p):
        """
        const_value_list : const_value_list const_value
        """
        p[0] = p[1] + [p[2]]

    def p_const_value_list_single(self, p):
        """
        const_value_list : const_value
        """
        p[0] = [p[1]]

    def p_object_value(self, p):
        """
        object_value : BRACE_L object_field_list BRACE_R
                     | BRACE_L BRACE_R
        """
        p[0] = p[2] if len(p) == 4 else {}

    def p_object_field_list(self, p):
        """
        object_field_list : object_field_list object_field
        """
        obj = p[1].copy()
        obj.update(p[2])
        p[0] = obj

    def p_object_field_list_single(self, p):
        """
        object_field_list : object_field
        """
        p[0] = p[1]

    def p_object_field(self, p):
        """
        object_field : name COLON value
        """
        p[0] = {p[1]: p[3]}

    def p_const_object_value(self, p):
        """
        const_object_value : BRACE_L const_object_field_list BRACE_R
                           | BRACE_L BRACE_R
        """
        p[0] = p[2] if len(p) == 4 else {}

    def p_const_object_field_list(self, p):
        """
        const_object_field_list : const_object_field_list const_object_field
        """
        obj = p[1].copy()
        obj.update(p[2])
        p[0] = obj

    def p_const_object_field_list_single(self, p):
        """
        const_object_field_list : const_object_field
        """
        p[0] = p[1]

    def p_const_object_field(self, p):
        """
        const_object_field : name COLON const_value
        """
        p[0] = {p[1]: p[3]}

    def p_type(self, p):
        """
        type : named_type
             | list_type
             | non_null_type
        """
        p[0] = p[1]

    def p_named_type(self, p):
        """
        named_type : name
        """
        p[0] = NamedType(name=p[1])

    def p_list_type(self, p):
        """
        list_type : BRACKET_L type BRACKET_R
        """
        p[0] = ListType(type=p[2])

    def p_non_null_type(self, p):
        """
        non_null_type : named_type BANG
                      | list_type BANG
        """
        p[0] = NonNullType(type=p[1])

    def p_error(self, token):
        if token is None:
            self.raise_syntax_error('Unexpected end of input')
        else:
            fragment = token.value
            if len(fragment) > 20:
                fragment = fragment[:17] + '...'
            self.raise_syntax_error(
                'Syntax error at %s' % repr(fragment),
                token=token,
            )

    def raise_syntax_error(self, message, token=None):
        if token is None:
            raise SyntaxError(message)
        lexer = token.lexer
        if callable(getattr(lexer, 'find_column', None)):
            column = lexer.find_column(token)
        else:
            column = None
        raise SyntaxError(
            message=message,
            value=token.value,
            line=token.lineno,
            column=column,
        )
