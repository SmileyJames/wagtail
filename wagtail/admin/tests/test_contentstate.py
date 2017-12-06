import json

from django.test import TestCase

from wagtail.admin.rich_text.converters.contentstate import ContentstateConverter


def content_state_equal(v1, v2):
    "Test whether two contentState structures are equal, ignoring 'key' properties"
    if type(v1) != type(v2):
        return False

    if type(v1) == dict:
        if set(v1.keys()) != set(v2.keys()):
            return False
        return all(
            k == 'key' or content_state_equal(v, v2[k])
            for k, v in v1.items()
        )
    elif type(v1) == list:
        if len(v1) != len(v2):
            return False
        return all(
            content_state_equal(a, b) for a, b in zip(v1, v2)
        )
    else:
        return v1 == v2


class TestHtmlToContentState(TestCase):
    def assertContentStateEqual(self, v1, v2):
        "Assert that two contentState structures are equal, ignoring 'key' properties"
        self.assertTrue(content_state_equal(v1, v2), "%r does not match %r" % (v1, v2))

    def test_paragraphs(self):
        converter = ContentstateConverter(features=[])
        result = json.loads(converter.from_database_format(
            '''
            <p>Hello world!</p>
            <p>Goodbye world!</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {'inlineStyleRanges': [], 'text': 'Hello world!', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'Goodbye world!', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
            ]
        })

    def test_unknown_block_becomes_paragraph(self):
        converter = ContentstateConverter(features=[])
        result = json.loads(converter.from_database_format(
            '''
            <foo>Hello world!</foo>
            <foo>I said hello world!</foo>
            <p>Goodbye world!</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {'inlineStyleRanges': [], 'text': 'Hello world!', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'I said hello world!', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'Goodbye world!', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
            ]
        })

    def test_bare_text_becomes_paragraph(self):
        converter = ContentstateConverter(features=[])
        result = json.loads(converter.from_database_format(
            '''
            before
            <p>paragraph</p>
            between
            <p>paragraph</p>
            after
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {'inlineStyleRanges': [], 'text': 'before', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'paragraph', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'between', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'paragraph', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'after', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
            ]
        })

    def test_ignore_unrecognised_tags_in_blocks(self):
        converter = ContentstateConverter(features=[])
        result = json.loads(converter.from_database_format(
            '''
            <p>Hello <foo>frabjuous</foo> world!</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {'inlineStyleRanges': [], 'text': 'Hello frabjuous world!', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
            ]
        })

    def test_inline_styles(self):
        converter = ContentstateConverter(features=['bold', 'italic'])
        result = json.loads(converter.from_database_format(
            '''
            <p>You <b>do <em>not</em> talk</b> about Fight Club.</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {
                    'inlineStyleRanges': [
                        {'offset': 4, 'length': 11, 'style': 'BOLD'}, {'offset': 7, 'length': 3, 'style': 'ITALIC'}
                    ],
                    'text': 'You do not talk about Fight Club.', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []
                },
            ]
        })

    def test_inline_styles_at_top_level(self):
        converter = ContentstateConverter(features=['bold', 'italic'])
        result = json.loads(converter.from_database_format(
            '''
            You <b>do <em>not</em> talk</b> about Fight Club.
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {
                    'inlineStyleRanges': [
                        {'offset': 4, 'length': 11, 'style': 'BOLD'}, {'offset': 7, 'length': 3, 'style': 'ITALIC'}
                    ],
                    'text': 'You do not talk about Fight Club.', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []
                },
            ]
        })

    def test_inline_styles_depend_on_features(self):
        converter = ContentstateConverter(features=['italic', 'just-made-it-up'])
        result = json.loads(converter.from_database_format(
            '''
            <p>You <b>do <em>not</em> talk</b> about Fight Club.</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {
                    'inlineStyleRanges': [
                        {'offset': 7, 'length': 3, 'style': 'ITALIC'}
                    ],
                    'text': 'You do not talk about Fight Club.', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []
                },
            ]
        })

    def test_ordered_list(self):
        converter = ContentstateConverter(features=['h1', 'ol', 'bold', 'italic'])
        result = json.loads(converter.from_database_format(
            '''
            <h1>The rules of Fight Club</h1>
            <ol>
                <li>You do not talk about Fight Club.</li>
                <li>You <b>do <em>not</em> talk</b> about Fight Club.</li>
            </ol>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {'inlineStyleRanges': [], 'text': 'The rules of Fight Club', 'depth': 0, 'type': 'header-one', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'You do not talk about Fight Club.', 'depth': 0, 'type': 'ordered-list-item', 'key': '00000', 'entityRanges': []},
                {
                    'inlineStyleRanges': [
                        {'offset': 4, 'length': 11, 'style': 'BOLD'}, {'offset': 7, 'length': 3, 'style': 'ITALIC'}
                    ],
                    'text': 'You do not talk about Fight Club.', 'depth': 0, 'type': 'ordered-list-item', 'key': '00000', 'entityRanges': []
                },
            ]
        })

    def test_nested_list(self):
        converter = ContentstateConverter(features=['h1', 'ul'])
        result = json.loads(converter.from_database_format(
            '''
            <h1>Shopping list</h1>
            <ul>
                <li>Milk</li>
                <li>
                    Flour
                    <ul>
                        <li>Plain</li>
                        <li>Self-raising</li>
                    </ul>
                </li>
                <li>Eggs</li>
            </ul>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {'inlineStyleRanges': [], 'text': 'Shopping list', 'depth': 0, 'type': 'header-one', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'Milk', 'depth': 0, 'type': 'unordered-list-item', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'Flour', 'depth': 0, 'type': 'unordered-list-item', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'Plain', 'depth': 1, 'type': 'unordered-list-item', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'Self-raising', 'depth': 1, 'type': 'unordered-list-item', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'Eggs', 'depth': 0, 'type': 'unordered-list-item', 'key': '00000', 'entityRanges': []},
            ]
        })

    def test_external_link(self):
        converter = ContentstateConverter(features=['link'])
        result = json.loads(converter.from_database_format(
            '''
            <p>an <a href="http://wagtail.io">external</a> link</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {
                '0': {'mutability': 'MUTABLE', 'type': 'LINK', 'data': {'url': 'http://wagtail.io'}}
            },
            'blocks': [
                {
                    'inlineStyleRanges': [], 'text': 'an external link', 'depth': 0, 'type': 'unstyled', 'key': '00000',
                    'entityRanges': [{'offset': 3, 'length': 8, 'key': 0}]
                },
            ]
        })