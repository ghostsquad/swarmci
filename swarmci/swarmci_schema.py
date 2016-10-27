# coding=utf-8
SCHEMA = {
    "definitions": {
        "single_command": {
            "type": "string",
            "minLength": 1
        },

        "command": {
            "anyOf": [
                {
                    "$ref": "#/definitions/single_command"
                },
                {
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/single_command"
                    },
                    "minItems": 1
                }
            ]
        }
    },

    "type": "object",
    "properties": {
        "stages": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "properties": {
                    "jobs": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "properties": {
                                "name":     {"type": "string"},
                                "image":    {"type": "string"},
                                "env":      {
                                    "type": "object"
                                },
                                "commands": {
                                    "$ref": "#/definitions/command"
                                },
                                "after_failure": {
                                    "$ref": "#/definitions/command"
                                },
                                "finally": {
                                    "$ref": "#/definitions/command"
                                }
                            },
                            "required": ["name", "commands"]
                        }
                    }
                },
                "required": ["name", "jobs"]
            }
        },
    },
    "required": ["stages"]
}
