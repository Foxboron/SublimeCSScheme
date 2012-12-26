# import tinycss
from tinycss.css21 import *

# Other notes on the tinycss codestyle vs this one:
# - The documentation is Sphinx-optimized, I'll try to adapt to the style.
# - tinycss previously had a max line lenght of 80, raised it to 10.

__all__ = [
    # from tinycss.css21
    'Stylesheet',
    'Declaration',
    'AtRule',
    'RuleSet',
    # from tinycss.css21 imported
    'TokenList',
    'ParseError',
    # from this file
    'NameRule',
    'UUIDRule',
    'OtherStringRule',
    'SettingsRule',
    'CSSchemeParser'
]


# I am not too sure why tinycss wraps :everything: in separate classes but let's do that too
class _StringRule(object):
    """A generic parsed @import rule. To be derived from.

        .. attribute:: at_keyword

            To be defined.

        .. attribute:: value

            The string value for this rule.
    """
    at_keyword = ''

    def __init__(self, value, line, column):
        self.value = value
        self.line  = line
        self.value = column

    def __repr__(self):
        return ('<{0.__class__.__name__} {0.line}:{0.column}'
                '{0.value}'.format(self))


class NameRule(_StringRule):
    """A parsed @name rule.

        .. attribute:: at_keyword

            Always ``'@name'``.
    """
    at_keyword = '@name'


class UUIDRule(_StringRule):
    """A parsed @uuid rule.

        .. attribute:: at_keyword

            Always ``'@uuid'``.
    """
    at_keyword = '@uuid'


class OtherStringRule(_StringRule):
    """A parsed @uuid rule.

        .. attribute:: at_keyword

            The at-keyword for this rule.
    """
    at_keyword = ''

    def __init__(self, keyword, value, line, column):
        self.at_keyword = keyword
        super(OtherStringRule, this).__init__(value, line, column)

    def __repr__(self):
        return ('<{0.__class__.__name__} {0.at_keyword} {0.line}:{0.column}'
                '{0.value}'.format(self))


class SettingsRule(object):
    """A parsed @settings rule.

        .. attribute:: at_keyword

            Always ``'@settings'``.

        .. attribute:: declarations

            A list of :class:`Declaration`, in source order.

        .. attribute:: at_rules

            The list of parsed at-rules inside the @settings block, in source order.
            Should not contain anything but string at-rules are valid.

    """
    at_keyword = '@page'

    def __init__(self, declarations, at_rules, line, column):
        self.declarations = declarations
        self.at_rules     = at_rules
        self.line         = line
        self.column       = column

    def __repr__(self):
        return ('<{0.__class__.__name__} {0.line}:{0.column}'.format(self))


class CSSchemeParser(CSS21Parser):
    """Documentation to be here.
    """

    def parse_at_rule(self, rule, previous_rules, errors, context):
        """Parse an at-rule.

            This method handles @uuid, @name, @settings and any other string rule
            Example:
                @author "I am not an author";

            :raises:
                :class:`~.parsing.ParseError` if the rule is invalid.

            :return:
                A parsed at-rule
        """
        # avoid duplicated code
        string_rules = {'@uuid': UUIDRule,
                        '@name': NameRule}

        if context == 'stylesheet' and rule.at_keyword in string_rules.keys():
            # check for previous @uuid/@name rule and context
            if context != 'stylesheet':
                raise ParseError(rule,
                    '{0} not allowed in {1}'.format(rule.at_keyword, context))
            for previous_rule in previous_rules:
                if previous_rule.at_keyword == rule.at_keyword:
                    raise ParseError(previous_rule,
                        '{0} only allowed once, previously line {1}'
                        .format(rule.at_keyword, previous_rule.line))
                    # TOCHECK: Does this consider other contexts?

            # check the value (format)
            head = rule.head
            if rule.body is not None:
                raise ParseError(head[-1], "expected ';', got a block")

            if not head:
                raise ParseError(rule,
                    'expected STRING token for {0} rule'.format(rule.at_keyword))
            if len(head) > 1:
                raise ParseError(head[1],
                    'expected 1 token for {0} rule, got {1}'.format(rule.at_keyword, len(head)))
            if head[0].type != 'STRING':
                raise ParseError(rule,
                    'expected STRING token for {0} rule, got {1}'
                    .format(rule.at_keyword, head[0].type))

            # TOCHECK: Probably does not remove "' around string
            return string_rules[rule.at_keyword](head[0].value, rule.line, rule.column)

        elif rule.at_keyword == '@settings':
            # context
            if context == '@settings':
                raise ParseError(rule,
                    '@settings rule not allowed in ' + context)
            # form
            if rule.head:
                raise ParseError(rule,
                    "invalid {0} rule: '{{' expected".format(rule.at_keyword))
            if rule.body is None:
                raise ParseError(rule,
                    'invalid {0} rule: missing block'.format(rule.at_keyword))
            # parse the declarations
            declarations, at_rules, rule_errors = \
                self.parse_declarations_and_at_rules(rule.body, '@settings')
            errors.extend(rule_errors)

            return SettingsRule(declarations, at_rules, rule.line, rule.column)

        # any at-rule with a string head and no body
        elif rule.head and rule.head[0].type == 'STRING' and rule.body is None:
            # each only once
            for previous_rule in previous_rules:
                if previous_rule.at_keyword == rule.at_keyword:
                    raise ParseError(previous_rule,
                        '{0} only allowed once, previously line {1}'
                        .format(rule.at_keyword, previous_rule.line))
                    # TOCHECK: Does this consider other contexts?

            if len(head) > 1:
                raise ParseError(head[1],
                    'expected 1 token for {0} rule, got {1}'.format(rule.at_keyword, len(head)))

            return OtherStringRule(rule.at_keyword, head[0].value, rule.line, rule.column)

        else:
            raise ParseError(rule,
                'invalid at-rule in {0} context: {1}'.format(context, rule.at_keyword))

    def parse_declarations_and_at_rules(self, tokens, context):
        """Parse a mixed list of declarations and at rules.

            This implementation only differs in forwarding the ``context``
            parameter to :meth:``parse_declaration``.
        """
        at_rules = []
        declarations = []
        errors = []
        tokens = iter(tokens)
        for token in tokens:
            if token.type == 'ATKEYWORD':
                try:
                    rule = self.read_at_rule(token, tokens)
                    result = self.parse_at_rule(
                        rule, at_rules, errors, context)
                    at_rules.append(result)
                except ParseError as err:
                    errors.append(err)
            elif token.type != 'S':
                declaration_tokens = []
                while token and token.type != ';':
                    declaration_tokens.append(token)
                    token = next(tokens, None)
                if declaration_tokens:
                    try:
                        # only change in this implementation:
                        declarations.append(
                            self.parse_declaration(declaration_tokens, context))
                    except ParseError as err:
                        errors.append(err)
        return declarations, at_rules, errors

    def parse_declaration(self, tokens, context=None):
        """Parse a single declaration. Considers context.

            :returns:
                a :class:`Declaration`
            :raises:
                :class:`~.parsing.ParseError` if the tokens do not match the
                'declaration' production of the core grammar.
        """
        tokens = iter(tokens)

        name_token = next(tokens)  # assume there is at least one
        if name_token.type == 'IDENT':
            # tmThemes are case-sensitive
            property_name = name_token.value
        else:
            raise ParseError(name_token,
                'expected a property name, got {0}'.format(name_token.type))

        # allowed properties in their respective scope
        if context == '@settings':
            allowed_properties = ('background', 'caret', 'foreground', 'invisibles',
                                  'lineHighlight', 'selection', 'findHighlight',
                                  'inactiveSelection', 'gutterForeground', 'guide',
                                  'activeGuide')
        else:
            allowed_properties = ('foreground', 'background', 'fontStyle')
        if property_name not in allowed_properties:
            raise ParseError(name_token,
                'property {0} invalid in {1}'.format(property_name, context))

        # proceed with value
        for token in tokens:
            if token.type == ':':
                break
            elif token.type != 'S':
                raise ParseError(
                    token, "expected ':', got {0}".format(token.type))
        else:
            raise ParseError(name_token, "expected ':'")

        value = strip_whitespace(list(tokens))
        if not value:
            raise ParseError(name_token, 'expected a property value')

        # validate the value
        # 'fontStyle' accepts IDENT and S, all others are exactly one HASH
        def invalid_value(type_, pname):
            raise ParseError(token,
                '{0} {1} token for property {2}'.format(
                    type_ in ('}', ')', ']') and 'unmatched' or 'unexpected', type_, pname))

        if property_name == 'fontStyle':
            for token in value:
                if token.type not in ('S', 'IDENT'):
                    invalid_value(token.type, property_name)
                if token.type == 'IDENT':
                    if token.value not in ('bold', 'italic', 'underline'):
                        raise ParseError(token,
                            "invalid value '{0}' for property {1}".format(token.value, property_name))
        elif len(value) > 1:
            ParseError(value[1],
                'expected 1 token for {0}, got {1}'.format(property_name, len(value)))
        elif value[0].type != 'HASH':
            invalid_value(value[0].type, property_name)

        # Note: '!important' priority not considered
        return Declaration(
            property_name, value, None, name_token.line, name_token.column)
