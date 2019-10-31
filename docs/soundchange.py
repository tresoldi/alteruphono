#!/usr/bin/env python
# -*- coding: utf-8 -*-

# CAVEAT UTILITOR
#
# This file was automatically generated by TatSu.
#
#    https://pypi.python.org/pypi/tatsu/
#
# Any changes you make to it will be overwritten the next time
# the file is generated.


from __future__ import print_function, division, absolute_import, unicode_literals

import sys

from tatsu.buffering import Buffer
from tatsu.parsing import Parser
from tatsu.parsing import tatsumasu, leftrec, nomemo
from tatsu.parsing import leftrec, nomemo  # noqa
from tatsu.util import re, generic_main  # noqa


KEYWORDS = {}  # type: ignore


class SOUND_CHANGEBuffer(Buffer):
    def __init__(
        self,
        text,
        whitespace=None,
        nameguard=None,
        comments_re=None,
        eol_comments_re=None,
        ignorecase=None,
        namechars='',
        **kwargs
    ):
        super(SOUND_CHANGEBuffer, self).__init__(
            text,
            whitespace=whitespace,
            nameguard=nameguard,
            comments_re=comments_re,
            eol_comments_re=eol_comments_re,
            ignorecase=ignorecase,
            namechars=namechars,
            **kwargs
        )


class SOUND_CHANGEParser(Parser):
    def __init__(
        self,
        whitespace=None,
        nameguard=None,
        comments_re=None,
        eol_comments_re=None,
        ignorecase=None,
        left_recursion=True,
        parseinfo=True,
        keywords=None,
        namechars='',
        buffer_class=SOUND_CHANGEBuffer,
        **kwargs
    ):
        if keywords is None:
            keywords = KEYWORDS
        super(SOUND_CHANGEParser, self).__init__(
            whitespace=whitespace,
            nameguard=nameguard,
            comments_re=comments_re,
            eol_comments_re=eol_comments_re,
            ignorecase=ignorecase,
            left_recursion=left_recursion,
            parseinfo=parseinfo,
            keywords=keywords,
            namechars=namechars,
            buffer_class=buffer_class,
            **kwargs
        )

    @tatsumasu()
    def _start_(self):  # noqa
        with self._choice():
            with self._option():
                self._sequence_()
                self.name_last_node('source')
                self._arrow_()
                self._sequence_()
                self.name_last_node('target')
                self._slash_()
                self._sequence_()
                self.name_last_node('context')
                self._check_eof()
            with self._option():
                self._sequence_()
                self.name_last_node('source')
                self._arrow_()
                self._sequence_()
                self.name_last_node('target')
                self._check_eof()
            self._error('no available options')
        self.ast._define(
            ['context', 'source', 'target'],
            []
        )

    @tatsumasu()
    def _sequence_(self):  # noqa

        def block0():
            self._segment_()
        self._positive_closure(block0)

    @tatsumasu()
    def _segment_(self):  # noqa
        with self._choice():
            with self._option():
                self._boundary_symbol_()
            with self._option():
                self._position_symbol_()
            with self._option():
                self._null_symbol_()
            with self._option():
                self._ipa_()
            with self._option():
                self._sound_class_()
            with self._option():
                self._feature_desc_()
            with self._option():
                self._back_ref_()
            with self._option():
                self._alternative_()
            self._error('no available options')

    @tatsumasu()
    def _feature_desc_(self):  # noqa
        with self._optional():
            self._token('*')
        self.name_last_node('recons')
        self._token('[')

        def sep1():
            self._token(',')

        def block1():
            self._feature_()
            self.name_last_node('feature_desc')
        self._positive_gather(block1, sep1)
        self._token(']')
        self.ast._define(
            ['feature_desc', 'recons'],
            []
        )

    @tatsumasu()
    def _feature_(self):  # noqa
        with self._choice():
            with self._option():
                self._feature_op_()
                self.name_last_node('value')
                self._feature_key_()
                self.name_last_node('key')
            with self._option():
                self._feature_key_()
                self.name_last_node('key')
                self._token('=')
                self._feature_value_()
                self.name_last_node('value')
            with self._option():
                self._feature_key_()
                self.name_last_node('key')
            self._error('no available options')
        self.ast._define(
            ['key', 'value'],
            []
        )

    @tatsumasu()
    def _feature_key_(self):  # noqa
        self._pattern('[a-z][a-z0-9_]+')

    @tatsumasu()
    def _feature_value_(self):  # noqa
        with self._choice():
            with self._option():
                self._token('true')
            with self._option():
                self._token('false')
            self._error('no available options')

    @tatsumasu()
    def _feature_op_(self):  # noqa
        with self._choice():
            with self._option():
                self._token('+')
            with self._option():
                self._token('-')
            with self._option():
                self._token('!')
            self._error('no available options')

    @tatsumasu()
    def _back_ref_(self):  # noqa
        with self._choice():
            with self._option():
                with self._optional():
                    self._token('*')
                self.name_last_node('recons')
                self._token('@')
                self._pattern('[0-9]+')
                self.name_last_node('back_ref')
                self._feature_desc_()
                self.name_last_node('modifier')
            with self._option():
                with self._optional():
                    self._token('*')
                self.name_last_node('recons')
                self._token('@')
                self._pattern('[0-9]+')
                self.name_last_node('back_ref')
            self._error('no available options')
        self.ast._define(
            ['back_ref', 'modifier', 'recons'],
            []
        )

    @tatsumasu()
    def _alternative_(self):  # noqa
        self._token('{')

        def sep0():
            self._token(',')

        def block0():
            self._sequence_()
            self.name_last_node('alternative')
        self._positive_gather(block0, sep0)
        self._token('}')
        self.ast._define(
            ['alternative'],
            []
        )

    @tatsumasu()
    def _arrow_(self):  # noqa
        with self._choice():
            with self._option():
                self._token('>')
            with self._option():
                self._token('->')
            with self._option():
                self._token('-->')
            with self._option():
                self._token('=>')
            with self._option():
                self._token('==>')
            with self._option():
                self._token('→')
            with self._option():
                self._token('⇒')
            with self._option():
                self._token('⇢')
            with self._option():
                self._token('⇾')
            with self._option():
                self._token('»')
            self._error('no available options')

    @tatsumasu()
    def _slash_(self):  # noqa
        with self._choice():
            with self._option():
                self._token('/')
            with self._option():
                self._token('//')
            self._error('no available options')

    @tatsumasu()
    def _boundary_symbol_(self):  # noqa
        self._token('#')
        self.name_last_node('boundary')
        self.ast._define(
            ['boundary'],
            []
        )

    @tatsumasu()
    def _position_symbol_(self):  # noqa
        self._token('_')
        self.name_last_node('position')
        self.ast._define(
            ['position'],
            []
        )

    @tatsumasu()
    def _null_symbol_(self):  # noqa
        with self._group():
            with self._choice():
                with self._option():
                    self._token('∅')
                with self._option():
                    self._token('0')
                with self._option():
                    self._token('ø')
                with self._option():
                    self._token('Ø')
                self._error('no available options')
        self.name_last_node('null')
        self.ast._define(
            ['null'],
            []
        )

    @tatsumasu()
    def _ipa_(self):  # noqa
        with self._optional():
            self._token('*')
        self.name_last_node('recons')
        self._pattern('ẽ̞ẽ̞|õ̞õ̞|ø̞̃ø̞̃|ɔ̞̈ɔ̞̈|ɞ̞̃ɞ̞̃|ɤ̞̃ɤ̞̃|ɪ̈̃ɪ̈̃|ɯ̽̃ɯ̽̃|ɵ̞̃ɵ̞̃|ʊ̈̃ʊ̈̃|d̪z̪ː|d̪ːz̪|t̠ʃʼː|t̪s̪ʰ|t̪s̪ʲ|t̪s̪ʼ|t̪s̪ː|t̪ɬ̪ʰ|t̪ɬ̪ʼ|t̪ːs̪|ãã|a̰ːː|cçʰ|dz̪ː|d̠ʒʷ|d̠ʒː|d̠ʒ̤|d̪z̪|d̪ʱː|d̪ːʱ|d̪̥̚|d̪̥ⁿ|ẽẽ|e̞e̞|ẽ̞ː|ĩĩ|ḭːː|õõ|o̞o̞|õ̞ː|ts̪ʰ|ts̪ʲ|ts̪ʼ|ts̪ː|tɬ̪ʰ|tɬ̪ʼ|tʃʼː|tːs̪|tːʃʼ|t̠ʃʰ|t̠ʃʷ|t̠ʃʼ|t̠ʃː|t̪s̪|t̪ɬ̪|t̪ʰʲ|t̪ʰː|t̪ʷʰ|t̪ːʰ|ũũ|ỹỹ|æ̃æ̃|ø̃ø̃|ø̞ø̞|ø̞̃ː|ŋgǀǀ|ŋgǃǃ|ŋ̊ǀǀ|ŋ̊ǃǃ|œ̃œ̃|ɐ̃ɐ̃|ɐ̹ɐ̹|ɑ̃ɑ̃|ɒ̃ɒ̃|ɔ̃ɔ̃|ɔ̞̈ː|ɘ̃ɘ̃|ə̃ə̃|ɛ̃ɛ̃|ɜ̃ɜ̃|ɞ̃ɞ̃|ɞ̞ɞ̞|ɞ̞̃ː|ɤ̃ɤ̃|ɤ̞ɤ̞|ɤ̞̃ː|ɨ̃ɨ̃|ɪ̃ɪ̃|ɪ̈ɪ̈|ɪ̈̃ː|ɯ̃ɯ̃|ɯ̽ɯ̽|ɯ̽̃ː|ɵ̃ɵ̃|ɵ̞ɵ̞|ɵ̞̃ː|ɶ̃ɶ̃|ʉ̃ʉ̃|ʊ̃ʊ̃|ʊ̈ʊ̈|ʊ̈̃ː|ʌ̃ʌ̃|ʏ̃ʏ̃|ʰt̪ʰ|ˀŋǀǀ|ˀŋǃǃ|ⁿgǀǀ|ⁿgǃǃ|ãː|bʰː|bʱː|bʷː|bːʰ|bːʱ|bːʷ|bːˤ|bˤː|b̥ʰ|cç|dzː|dz̪|dʑː|dʒʱ|dʒʲ|dʒʷ|dʰː|dʱː|dːz|dːʑ|dːʒ|dːʰ|dːʱ|d̠ʒ|d̤ʒ|d̤ː|d̥̚|d̥ⁿ|d̪ð|d̪ɮ|d̪ʱ|d̪ʲ|d̪ː|d̪ˠ|d̪ˤ|d̪̈|d̪̚|d̪̤|d̪̰|d̪ⁿ|eːː|ẽː|e̞ː|e̞ˑ|ẽ̞|e̹ː|fʷː|fːʷ|gǃǃ|g̊ʰ|iːː|ĩː|ḭː|kwh|kǃǃ|kʷʰ|kʷʼ|kʷː|kʼʷ|k\uf268ʼ|l̠ʲ|l̪ʲ|l̪ː|l̪̍|l̪̥|l̪̩|mʷː|mːʷ|mːˤ|mˤː|n̪ˠ|oz̻|oːː|õː|o̞ː|õ̞|pfʰ|pfʼ|pʰʲ|pʰː|pːʰ|qʰʷ|qʷʰ|qʷʼ|qʼʷ|qʼ↓|rːˤ|rˤː|r̪ː|r̪ˤ|r̪̥|s̪ʲ|s̪ʼ|s̪ˠ|tsʰ|tsʲ|tsʼ|tsː|ts̪|tɕʰ|tɕː|tɬʰ|tɬʼ|tɬ̪|tʂʰ|tʂː|tʃʰ|tʃʲ|tʃʷ|tʃʼ|tʃː|tʰʷ|tʲʰ|tʷʰ|tːs|tːɕ|tːʂ|tːʃ|t̠ʃ|t̪ʰ|t̪ʲ|t̪ʷ|t̪ʼ|t̪ː|t̪ˠ|t̪ˤ|t̪̚|t̪θ|t̪ⁿ|uːː|ũː|yːː|ỹː|z̪̥|²²³|²²¹|²²⁴|²²⁵|²³²|²³³|²³¹|²¹²|²¹³|²¹¹|²¹⁴|²¹⁵|²⁴²|²⁴³|²⁴¹|²⁴⁴|²⁵²|²⁵³|²⁵¹|²⁵⁴|²⁵⁵|³²²|³²³|³²⁴|³²⁵|³³²|³³¹|³³⁴|³³⁵|³¹²|³¹³|³¹¹|³¹⁴|³¹⁵|³⁴²|³⁴³|³⁴¹|³⁴⁴|³⁴⁵|³⁵²|³⁵³|³⁵¹|³⁵⁴|³⁵⁵|¹²²|¹²¹|¹³²|¹³³|¹³¹|¹¹²|¹¹³|¹¹⁴|¹¹⁵|¹⁴²|¹⁴³|¹⁴¹|¹⁴⁴|¹⁵²|¹⁵³|¹⁵¹|¹⁵⁴|¹⁵⁵|æːː|æ̃ː|øːː|ø̃ː|ø̞ː|ø̞̃|ŋgǀ|ŋgǁ|ŋgǂ|ŋgǃ|ŋgʘ|ŋǀǀ|ŋǃǃ|ŋ̊ǀ|ŋ̊ǁ|ŋ̊ǂ|ŋ̊ǃ|ŋ̊ʘ|œ̃ː|ɐ̃ː|ɐ̹ː|ɑ̃ː|ɒ̃ː|ɔ̃ː|ɔ̞̈|ɖːʐ|ɘ̃ː|ə̃ː|ɛːː|ɛ̃ː|ɛ̹̃|ɜ̃ː|ɞ̃ː|ɞ̞ː|ɞ̞̃|ɤ̃ː|ɤ̞ː|ɤ̞̃|ɨ̃ː|ɪ̃ː|ɪ̈ː|ɪ̈̃|ɬ̪ʼ|ɯ̃ː|ɯ̥̃|ɯ̽ː|ɯ̽̃|ɵ̃ː|ɵ̞ː|ɵ̞̃|ɶ̃ː|ʈʂʰ|ʈʂː|ʈʂ’|ʈʰː|ʈːʂ|ʈːʰ|ʉ̃ː|ʊ̃ː|ʊ̈ː|ʊ̈̃|ʌ̃ː|ʌ̤̃|ʌ̯ː|ʏ̃ː|ʰtʰ|ʰt̪|ˀŋǀ|ˀŋǁ|ˀŋǂ|ˀŋǃ|ˀŋʘ|⁴²²|⁴²³|⁴²⁴|⁴²⁵|⁴³³|⁴³⁴|⁴³⁵|⁴¹²|⁴¹³|⁴¹¹|⁴¹⁴|⁴¹⁵|⁴⁴²|⁴⁴³|⁴⁴¹|⁴⁴⁵|⁴⁵²|⁴⁵³|⁴⁵¹|⁴⁵⁴|⁴⁵⁵|⁵²²|⁵²³|⁵²⁴|⁵²⁵|⁵³³|⁵³⁴|⁵³⁵|⁵¹²|⁵¹³|⁵¹¹|⁵¹⁴|⁵¹⁵|⁵⁴⁴|⁵⁴⁵|⁵⁵²|⁵⁵³|⁵⁵¹|⁵⁵⁴|ⁿdʒ|ⁿd̪|ⁿd̼|ⁿgǀ|ⁿgǁ|ⁿgǂ|ⁿgǃ|ⁿgʘ|ⁿkʷ|ⁿtʃ|ⁿt̪|aa|aː|aˑ|a˞|ã|ă|ḁ|a̯|a̰|bv|bʰ|bʱ|bʲ|bʷ|bː|bˠ|b̚|b̡|b̤|b̥|b̪|bβ|bᵛ|bᵝ|bⁿ|cʰ|cʼ|cː|ç|dz|dð|dɮ|dʐ|dʑ|dʒ|dʰ|dʱ|dʲ|dː|dˤ|d̂|d̠|d̤|d̥|d̪|d̰|d̼|dᶞ|dᶻ|dᶼ|dᶽ|dⁿ|ee|eː|eˑ|ẽ|ĕ|e̞|e̤|e̥|e̯|ḛ|e̹|fʰ|fʲ|fʼ|fˈ|fː|fˠ|gǀ|gǁ|gǂ|gǃ|gɣ|gʘ|gʰ|gʱ|gʲ|gʷ|gː|gˠ|g̈|g̊|g̥|h̃|h̬|ii|iː|iˑ|ĩ|i̤|i̥|ḭ|i̹|jː|j̃|j̊|j̥|kh|kw|kx|kǀ|kǁ|kǂ|kǃ|kʘ|kʰ|kʲ|kʷ|kʼ|kː|kˣ|k̚|k̬|k\uf268|lʱ|lʲ|lː|lˠ|l̂|l̠|ḷ|l̤|l̥|l̩|l̪|l̻|l̼|mʰ|mʱ|mʲ|mʷ|mː|mˠ|ṃ|m̤|m̥|m̩|nʲ|nː|nˤ|n̂|ñ|n̊|ṇ|n̥|n̩|n̪|n̰|n̻|n̼|oo|oː|oˑ|oˤ|õ|ŏ|o̞|o̤|o̥|o̯|o̰|pf|ph|pɸ|pʰ|pʲ|pʷ|pʼ|pː|pˠ|p̚|p̪|p̬|pᶠ|pᶲ|qʰ|qʷ|qʼ|q̚|qχ|qᵡ|rʲ|rː|rˤ|r̃|r̥|r̩|r̪|r̼|sʲ|sʼ|sː|sˠ|s̩|s̪|s̬|s̻|th|ts|tɕ|tɬ|tʂ|tʃ|tʰ|tʲ|tʷ|tʼ|tː|tˢ|tˤ|t̂|t̚|t̠|t̪|t̬|t̼|tθ|tᶝ|tᶳ|tᶴ|tᶿ|tⁿ|uu|uː|uˑ|ũ|ṳ|u̥|ṵ|vʲ|vː|v̆|v̥|v̩|wː|wˠ|w̃|xʲ|xʷ|xʼ|ẋ|yy|yː|yˑ|ỹ|zʲ|z̥|z̩|z̪|²²|²³|²¹|²⁴|²⁵|³²|³³|³¹|³⁴|³⁵|¹²|¹³|¹¹|¹⁴|¹⁵|ææ|æː|æˑ|æ̃|æ̰|ðː|ð̚|ð̞|ð̼|ð͉|øø|øː|øˑ|ø̃|ø̞|ŋǀ|ŋǁ|ŋǂ|ŋǃ|ŋʘ|ŋʷ|ŋː|ŋ̊|ŋ̍|ŋ̥|ŋ̩|œœ|œː|œ̃|ȵ̊|ɐɐ|ɐː|ɐ̃|ɐ̯|ɐ̹|ɑɑ|ɑː|ɑ̃|ɑ̟|ɒɒ|ɒː|ɒ̃|ɓʲ|ɔɔ|ɔː|ɔ̃|ɔ̑|ɔ̯|ɔ̰|ɖʐ|ɖʱ|ɖ̤|ɖᶼ|ɗ̥|ɘɘ|ɘː|ɘ̃|əə|əː|ə˞|ə̃|ə̆|ə̰|ɛɛ|ɛː|ɛ̃|ɛ̑|ɛ̯|ɛ̰|ɜɜ|ɜː|ɜ̃|ɞɞ|ɞː|ɞ̃|ɞ̞|ɟʝ|ɡ̤|ɢʁ|ɢʰ|ɢʶ|ɣʷ|ɣ̊|ɣ̥|ɤɤ|ɤː|ɤ̃|ɤ̆|ɤ̑|ɤ̞|ɤ̯|ɨɨ|ɨː|ɨ̃|ɪɪ|ɪː|ɪ̃|ɪ̈|ɪ̥|ɪ̯|ɪ̰|ɪ̹|ɬʼ|ɬ̪|ɬ̼|ɭ̊|ɭ̍|ɭ̩|ɮ̼|ɯɯ|ɯː|ɯ̃|ɯ̤|ɯ̥|ɯ̯|ɯ̽|ɱ̊|ɱ̥|ɲː|ɲ̊|ɲ̍|ɲ̥|ɳ̊|ɳ̍|ɴ̥|ɴ̩|ɵɵ|ɵː|ɵ̃|ɵ̞|ɶɶ|ɶː|ɶ̃|ɹ̠|ɹ̩|ɽʱ|ɽ̈|ɾ̥|ɾ̼|ʀ̥|ʁ̞|ʁ̥|ʃʲ|ʃʼ|ʇ̼|ʈʂ|ʈʰ|ʈ̬|ʈᶳ|ʉʉ|ʉː|ʉ̃|ʉ̰|ʊʊ|ʊː|ʊ̃|ʊ̈|ʊ̥|ʊ̯|ʊ̰|ʌʌ|ʌː|ʌ̃|ʌ̆|ʌ̤|ʎ̟|ʎ̥|ʏʏ|ʏː|ʏ̃|ʒ̊|ʒ̍|ʒ̩|ʔh|ʔʲ|ʔʷ|ʙ̥|ʙ̩|ʛ̥|ʟ̥|ʦː|ʰk|ʰp|ʰt|βʷ|β̞|θː|θ̬|θ̼|χʷ|χʼ|⁴²|⁴³|⁴¹|⁴⁴|⁴⁵|⁵²|⁵³|⁵¹|⁵⁴|⁵⁵|ⁿb|ⁿd|ⁿg|ⁿk|ⁿp|ⁿt|ⁿɟ|a|b|c|d|e|f|g|h|i|j|k|l|m|n|o|p|q|r|s|t|u|v|w|x|y|z|²|³|¹|æ|ð|ø|ħ|ŋ|œ|ƛ|ƫ|ǀ|ǁ|ǂ|ǃ|ȡ|ȴ|ȵ|ȶ|ɐ|ɑ|ɒ|ɓ|ɔ|ɕ|ɖ|ɗ|ɘ|ə|ɛ|ɜ|ɞ|ɟ|ɠ|ɢ|ɣ|ɤ|ɥ|ɦ|ɧ|ɨ|ɪ|ɫ|ɬ|ɭ|ɮ|ɯ|ɰ|ɱ|ɲ|ɳ|ɴ|ɵ|ɶ|ɸ|ɹ|ɺ|ɻ|ɽ|ɾ|ɿ|ʀ|ʁ|ʂ|ʃ|ʄ|ʅ|ʆ|ʈ|ʉ|ʊ|ʋ|ʌ|ʍ|ʎ|ʏ|ʐ|ʑ|ʒ|ʔ|ʕ|ʘ|ʙ|ʛ|ʜ|ʝ|ʟ|ʠ|ʡ|ʢ|ʣ|ʤ|ʥ|ʦ|ʧ|ʨ|ʮ|ʯ|β|θ|χ|ᴀ|ᶀ|ᶁ|ᶂ|ᶃ|ᶄ|ᶅ|ᶆ|ᶇ|ᶈ|ᶉ|ᶊ|ᶋ|ᶌ|ᶍ|ᶎ|ᶑ|⁰|⁴|⁵|ⱱ')
        self.name_last_node('ipa')
        self.ast._define(
            ['ipa', 'recons'],
            []
        )

    @tatsumasu()
    def _sound_class_(self):  # noqa
        with self._optional():
            self._token('*')
        self.name_last_node('recons')
        self._pattern('[A-Z][A-Z0-9]*')
        self.name_last_node('sound_class')
        self.ast._define(
            ['recons', 'sound_class'],
            []
        )


class SOUND_CHANGESemantics(object):
    def start(self, ast):  # noqa
        return ast

    def sequence(self, ast):  # noqa
        return ast

    def segment(self, ast):  # noqa
        return ast

    def feature_desc(self, ast):  # noqa
        return ast

    def feature(self, ast):  # noqa
        return ast

    def feature_key(self, ast):  # noqa
        return ast

    def feature_value(self, ast):  # noqa
        return ast

    def feature_op(self, ast):  # noqa
        return ast

    def back_ref(self, ast):  # noqa
        return ast

    def alternative(self, ast):  # noqa
        return ast

    def arrow(self, ast):  # noqa
        return ast

    def slash(self, ast):  # noqa
        return ast

    def boundary_symbol(self, ast):  # noqa
        return ast

    def position_symbol(self, ast):  # noqa
        return ast

    def null_symbol(self, ast):  # noqa
        return ast

    def ipa(self, ast):  # noqa
        return ast

    def sound_class(self, ast):  # noqa
        return ast


def main(filename, start=None, **kwargs):
    if start is None:
        start = 'start'
    if not filename or filename == '-':
        text = sys.stdin.read()
    else:
        with open(filename) as f:
            text = f.read()
    parser = SOUND_CHANGEParser()
    return parser.parse(text, rule_name=start, filename=filename, **kwargs)


if __name__ == '__main__':
    import json
    from tatsu.util import asjson

    ast = generic_main(main, SOUND_CHANGEParser, name='SOUND_CHANGE')
    print('AST:')
    print(ast)
    print()
    print('JSON:')
    print(json.dumps(asjson(ast), indent=2))
    print()
