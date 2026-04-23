# Documind Skills

This directory contains project-specific skills for the documind project.

## What are Skills?

Skills are reusable instruction sets that can be invoked when specific tasks are needed. They help maintain consistency and capture best practices for common operations.

## Available Skills

### `documind-converter`

Converts `.docx` files to Markdown format optimized for LLM/RAG workflows.

**When to use:** When you need to convert Word documents to markdown, extract content from .docx files, or process documents for AI/ML workflows.

## How to Use

Skills in this directory can be referenced by name when working with Claude Code or similar tools.

## Adding New Skills

To add a new skill:

1. Create a new directory under `skills/`
2. Add a `SKILL.md` file with frontmatter:
   ```yaml
   ---
   name: skill-name
   description: When to trigger this skill
   ---
   ```
3. Document the skill's purpose and usage
