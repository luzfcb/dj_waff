from __future__ import unicode_literals

try:
    from django.forms.widgets import RadioChoiceInput, RadioFieldRenderer, ChoiceFieldRenderer, RadioSelect
except ImportError:
    from itertools import chain
    import copy
    from django.conf import settings
    from django.utils.encoding import (
        force_str, force_text, python_2_unicode_compatible,
    )

    from django.utils.html import conditional_escape, format_html, html_safe
    from django.utils.safestring import mark_safe
    from django.forms.utils import flatatt
    from django.utils import six
    from django.forms.widgets import Select
    from django.utils.six.moves.urllib.parse import urljoin

    __all__ = (
        'SubWidget',
        'RadioSelect',
        'ChoiceInput',
        'RadioChoiceInput',
        'ChoiceFieldRenderer',
        'RadioFieldRenderer'
    )


    class RendererMixin(object):
        renderer = None  # subclasses must define this
        _empty_value = None

        def __init__(self, *args, **kwargs):
            # Override the default renderer if we were passed one.
            renderer = kwargs.pop('renderer', None)
            if renderer:
                self.renderer = renderer
            super(RendererMixin, self).__init__(*args, **kwargs)

        def subwidgets(self, name, value, attrs=None):
            for widget in self.get_renderer(name, value, attrs):
                yield widget

        def get_renderer(self, name, value, attrs=None):
            """Returns an instance of the renderer."""
            if value is None:
                value = self._empty_value
            final_attrs = self.build_attrs(attrs)
            return self.renderer(name, value, final_attrs, self.choices)

        def render(self, name, value, attrs=None):
            return self.get_renderer(name, value, attrs).render()

        def id_for_label(self, id_):
            # Widgets using this RendererMixin are made of a collection of
            # subwidgets, each with their own <label>, and distinct ID.
            # The IDs are made distinct by a "_X" suffix, where X is the zero-based
            # index of the choice field. Thus, the label for the main widget should
            # reference the first subwidget, hence the "_0" suffix.
            if id_:
                id_ += '_0'
            return id_


    @html_safe
    @python_2_unicode_compatible
    class SubWidget(object):
        """
        Some widgets are made of multiple HTML elements -- namely, RadioSelect.
        This is a class that represents the "inner" HTML element of a widget.
        """

        def __init__(self, parent_widget, name, value, attrs, choices):
            self.parent_widget = parent_widget
            self.name, self.value = name, value
            self.attrs, self.choices = attrs, choices

        def __str__(self):
            args = [self.name, self.value, self.attrs]
            if self.choices:
                args.append(self.choices)


    @html_safe
    @python_2_unicode_compatible
    class ChoiceInput(SubWidget):
        """
        An object used by ChoiceFieldRenderer that represents a single
        <input type='$input_type'>.
        """
        input_type = None  # Subclasses must define this

        def __init__(self, name, value, attrs, choice, index):
            self.name = name
            self.value = value
            self.attrs = attrs
            self.choice_value = force_text(choice[0])
            self.choice_label = force_text(choice[1])
            self.index = index
            if 'id' in self.attrs:
                self.attrs['id'] += "_%d" % self.index

        def __str__(self):
            return self.render()

        def render(self, name=None, value=None, attrs=None):
            if self.id_for_label:
                label_for = format_html(' for="{}"', self.id_for_label)
            else:
                label_for = ''
            attrs = dict(self.attrs, **attrs) if attrs else self.attrs
            return format_html(
                '<label{}>{} {}</label>', label_for, self.tag(attrs), self.choice_label
            )

        def is_checked(self):
            return self.value == self.choice_value

        def tag(self, attrs=None):
            attrs = attrs or self.attrs
            final_attrs = dict(attrs, type=self.input_type, name=self.name, value=self.choice_value)
            if self.is_checked():
                final_attrs['checked'] = 'checked'
            return format_html('<input{} />', flatatt(final_attrs))

        @property
        def id_for_label(self):
            return self.attrs.get('id', '')


    class RadioChoiceInput(ChoiceInput):
        input_type = 'radio'

        def __init__(self, *args, **kwargs):
            super(RadioChoiceInput, self).__init__(*args, **kwargs)
            self.value = force_text(self.value)


    @html_safe
    @python_2_unicode_compatible
    class ChoiceFieldRenderer(object):
        """
        An object used by RadioSelect to enable customization of radio widgets.
        """

        choice_input_class = None
        outer_html = '<ul{id_attr}>{content}</ul>'
        inner_html = '<li>{choice_value}{sub_widgets}</li>'

        def __init__(self, name, value, attrs, choices):
            self.name = name
            self.value = value
            self.attrs = attrs
            self.choices = choices

        def __getitem__(self, idx):
            return list(self)[idx]

        def __iter__(self):
            for idx, choice in enumerate(self.choices):
                yield self.choice_input_class(self.name, self.value, self.attrs.copy(), choice, idx)

        def __str__(self):
            return self.render()

        def render(self):
            """
            Outputs a <ul> for this set of choice fields.
            If an id was given to the field, it is applied to the <ul> (each
            item in the list will get an id of `$id_$i`).
            """
            id_ = self.attrs.get('id')
            output = []
            for i, choice in enumerate(self.choices):
                choice_value, choice_label = choice
                if isinstance(choice_label, (tuple, list)):
                    attrs_plus = self.attrs.copy()
                    if id_:
                        attrs_plus['id'] += '_{}'.format(i)
                    sub_ul_renderer = self.__class__(
                        name=self.name,
                        value=self.value,
                        attrs=attrs_plus,
                        choices=choice_label,
                    )
                    sub_ul_renderer.choice_input_class = self.choice_input_class
                    output.append(format_html(
                        self.inner_html, choice_value=choice_value,
                        sub_widgets=sub_ul_renderer.render(),
                    ))
                else:
                    w = self.choice_input_class(self.name, self.value, self.attrs.copy(), choice, i)
                    output.append(format_html(self.inner_html, choice_value=force_text(w), sub_widgets=''))
            return format_html(
                self.outer_html,
                id_attr=format_html(' id="{}"', id_) if id_ else '',
                content=mark_safe('\n'.join(output)),
            )


    class RadioFieldRenderer(ChoiceFieldRenderer):
        choice_input_class = RadioChoiceInput


    MEDIA_TYPES = ('css', 'js')


    @html_safe
    @python_2_unicode_compatible
    class Media(object):
        def __init__(self, media=None, **kwargs):
            if media:
                media_attrs = media.__dict__
            else:
                media_attrs = kwargs

            self._css = {}
            self._js = []

            for name in MEDIA_TYPES:
                getattr(self, 'add_' + name)(media_attrs.get(name, None))

        def __str__(self):
            return self.render()

        def render(self):
            return mark_safe('\n'.join(chain(*[getattr(self, 'render_' + name)() for name in MEDIA_TYPES])))

        def render_js(self):
            return [
                format_html(
                    '<script type="text/javascript" src="{}"></script>',
                    self.absolute_path(path)
                ) for path in self._js
                ]

        def render_css(self):
            # To keep rendering order consistent, we can't just iterate over items().
            # We need to sort the keys, and iterate over the sorted list.
            media = sorted(self._css.keys())
            return chain(*[[
                               format_html(
                                   '<link href="{}" type="text/css" media="{}" rel="stylesheet" />',
                                   self.absolute_path(path), medium
                               ) for path in self._css[medium]
                               ] for medium in media])

        def absolute_path(self, path, prefix=None):
            if path.startswith(('http://', 'https://', '/')):
                return path
            if prefix is None:
                if settings.STATIC_URL is None:
                    # backwards compatibility
                    prefix = settings.MEDIA_URL
                else:
                    prefix = settings.STATIC_URL
            return urljoin(prefix, path)

        def __getitem__(self, name):
            "Returns a Media object that only contains media of the given type"
            if name in MEDIA_TYPES:
                return Media(**{str(name): getattr(self, '_' + name)})
            raise KeyError('Unknown media type "%s"' % name)

        def add_js(self, data):
            if data:
                for path in data:
                    if path not in self._js:
                        self._js.append(path)

        def add_css(self, data):
            if data:
                for medium, paths in data.items():
                    for path in paths:
                        if not self._css.get(medium) or path not in self._css[medium]:
                            self._css.setdefault(medium, []).append(path)

        def __add__(self, other):
            combined = Media()
            for name in MEDIA_TYPES:
                getattr(combined, 'add_' + name)(getattr(self, '_' + name, None))
                getattr(combined, 'add_' + name)(getattr(other, '_' + name, None))
            return combined

    def media_property(cls):
        def _media(self):
            # Get the media property of the superclass, if it exists
            sup_cls = super(cls, self)
            try:
                base = sup_cls.media
            except AttributeError:
                base = Media()

            # Get the media definition for this class
            definition = getattr(cls, 'Media', None)
            if definition:
                extend = getattr(definition, 'extend', True)
                if extend:
                    if extend is True:
                        m = base
                    else:
                        m = Media()
                        for medium in extend:
                            m = m + base[medium]
                    return m + Media(definition)
                else:
                    return Media(definition)
            else:
                return base

        return property(_media)

    class MediaDefiningClass(type):
        """
        Metaclass for classes that can have media definitions.
        """

        def __new__(mcs, name, bases, attrs):
            new_class = (super(MediaDefiningClass, mcs)
                         .__new__(mcs, name, bases, attrs))

            if 'media' not in attrs:
                new_class.media = media_property(new_class)

            return new_class

    class Widget(six.with_metaclass(MediaDefiningClass)):
        needs_multipart_form = False  # Determines does this widget need multipart form
        is_localized = False
        is_required = False

        def __init__(self, attrs=None):
            if attrs is not None:
                self.attrs = attrs.copy()
            else:
                self.attrs = {}

        def __deepcopy__(self, memo):
            obj = copy.copy(self)
            obj.attrs = self.attrs.copy()
            memo[id(self)] = obj
            return obj

        @property
        def is_hidden(self):
            return self.input_type == 'hidden' if hasattr(self, 'input_type') else False

        def subwidgets(self, name, value, attrs=None, choices=()):
            """
            Yields all "subwidgets" of this widget. Used only by RadioSelect to
            allow template access to individual <input type="radio"> buttons.
            Arguments are the same as for render().
            """
            yield SubWidget(self, name, value, attrs, choices)

        def render(self, name, value, attrs=None):
            """
            Returns this Widget rendered as HTML, as a Unicode string.
            The 'value' given is not guaranteed to be valid input, so subclass
            implementations should program defensively.
            """
            raise NotImplementedError('subclasses of Widget must provide a render() method')

        def build_attrs(self, extra_attrs=None, **kwargs):
            "Helper function for building an attribute dictionary."
            attrs = dict(self.attrs, **kwargs)
            if extra_attrs:
                attrs.update(extra_attrs)
            return attrs

        def value_from_datadict(self, data, files, name):
            """
            Given a dictionary of data and this widget's name, returns the value
            of this widget. Returns None if it's not provided.
            """
            return data.get(name, None)

        def id_for_label(self, id_):
            """
            Returns the HTML ID attribute of this Widget for use by a <label>,
            given the ID of the field. Returns None if no ID is available.
            This hook is necessary because some widgets have multiple HTML
            elements and, thus, multiple IDs. In that case, this method should
            return an ID value that corresponds to the first ID in the widget's
            tags.
            """
            return id_

    class Select(Widget):
        allow_multiple_selected = False

        def __init__(self, attrs=None, choices=()):
            super(Select, self).__init__(attrs)
            # choices can be any iterable, but we may need to render this widget
            # multiple times. Thus, collapse it into a list so it can be consumed
            # more than once.
            self.choices = list(choices)

        def render(self, name, value, attrs=None, choices=()):
            if value is None:
                value = ''
            final_attrs = self.build_attrs(attrs, name=name)
            output = [format_html('<select{}>', flatatt(final_attrs))]
            options = self.render_options(choices, [value])
            if options:
                output.append(options)
            output.append('</select>')
            return mark_safe('\n'.join(output))

        def render_option(self, selected_choices, option_value, option_label):
            if option_value is None:
                option_value = ''
            option_value = force_text(option_value)
            if option_value in selected_choices:
                selected_html = mark_safe(' selected="selected"')
                if not self.allow_multiple_selected:
                    # Only allow for a single selection.
                    selected_choices.remove(option_value)
            else:
                selected_html = ''
            return format_html('<option value="{}"{}>{}</option>',
                               option_value,
                               selected_html,
                               force_text(option_label))

        def render_options(self, choices, selected_choices):
            # Normalize to strings.
            selected_choices = set(force_text(v) for v in selected_choices)
            output = []
            for option_value, option_label in chain(self.choices, choices):
                if isinstance(option_label, (list, tuple)):
                    output.append(format_html('<optgroup label="{}">', force_text(option_value)))
                    for option in option_label:
                        output.append(self.render_option(selected_choices, *option))
                    output.append('</optgroup>')
                else:
                    output.append(self.render_option(selected_choices, option_value, option_label))
            return '\n'.join(output)

    class RadioSelect(RendererMixin, Select):
        renderer = RadioFieldRenderer
        _empty_value = ''
