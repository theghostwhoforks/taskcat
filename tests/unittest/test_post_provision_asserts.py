import operator
import unittest
from functools import reduce

import yaml


class TestPostProvisionAssertion(unittest.TestCase):
    def test_should_parse_assertion_from_config(self):
        yaml_snippet = """
---
assertions:
    -   request: 
            method: GET
            url: "{{ CFN_LOADBALANCER_URL}}/status"
            protocol: http
            port: 80
        response:
            equals:
                - name: status_code
                  value: 200
            contains:
                - name: body
                  value: first_run
"""
        yaml_definition = yaml.safe_load(yaml_snippet)
        assertions = yaml_definition.get("assertions")
        self.assertEqual(1, len(assertions))

        first_assertion = assertions[0]
        request_to_perform = Request(**first_assertion["request"])

        self.assertEqual("GET", request_to_perform.method)
        self.assertEqual("http", request_to_perform.protocol)
        self.assertEqual("{{ CFN_LOADBALANCER_URL}}/status", request_to_perform.url)
        self.assertEqual(80, request_to_perform.port)

        response_assertion = Response(first_assertion["response"])
        self.assertEqual(2, len(response_assertion.matchers))

        self.assertEqual("status_code", response_assertion.matchers[0].property_name)
        self.assertEqual(200, response_assertion.matchers[0].expected_value)


class Request(object):
    def __init__(self, method, url, protocol, port):
        self.method = method
        self.url = url
        self.protocol = protocol
        self.port = port


class Response(object):
    matcher_strategy = {
        "equals": lambda prop_name, expected: Matcher(operator.eq, prop_name, expected),
        "contains": lambda prop_name, expected: Matcher(operator.contains, prop_name, expected)
    }

    @classmethod
    def build_matcher(cls, matcher_name, conditions):
        matcher_func = cls.matcher_strategy.get(matcher_name)
        [print(condition["name"], condition["value"]) for condition in conditions]
        return [matcher_func(condition["name"], condition["value"]) for condition in conditions]

    def __init__(self, matchers=None):
        if matchers is None:
            self.matchers = {}
        else:
            self.matchers = reduce(operator.concat, [Response.build_matcher(matcher_name, conditions)
                                                     for matcher_name, conditions in matchers.items()])


class Matcher(object):
    def __init__(self, op, property_name, expected_value):
        self.op = op
        self.property_name = property_name
        self.expected_value = expected_value
