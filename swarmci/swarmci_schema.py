# coding=utf-8
command_schema = {
    "type": "string",
    "minLength": 1
}

commands_schema = {
    "anyOf": [
        command_schema,
        {
            "type": "array",
            "items": command_schema,
            "minItems": 1
        }
    ]
}

job_schema = {
    "type": "object",
    "properties": {
        "name":     {"type": "string"},
        "image":    {"type": "string"},
        "env":      {
            "type": "object"
        },
        "commands": commands_schema,
        "after_failure": commands_schema,
        "finally": commands_schema
    },
    "required": ["name", "commands"]
}

jobs_schema = {
    "type": "array",
    "minItems": 1,
    "items": job_schema
}

stage_schema = {
    "type": "object",
    "properties": {
        "jobs": jobs_schema
    },
    "required": ["name", "jobs"]
}

stages_schema = {
    "type": "array",
    "minItems": 1,
    "items": stage_schema
}

SCHEMA = {
    "type": "object",
    "properties": {
        "stages": stages_schema
    },
    "required": ["stages"]
}
